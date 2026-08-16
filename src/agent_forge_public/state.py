"""Tenant-scoped memory, checkpoints, and immutable artifact references."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable, Mapping

from .contracts import ArtifactRef, LifecycleState, TERMINAL_STATES


class TenantBoundaryError(PermissionError):
    pass


class InvalidTransition(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    record_id: str
    tenant_id: str
    session_id: str
    role: str
    content: str
    created_at: float


@dataclass(frozen=True, slots=True)
class CheckpointRecord:
    run_id: str
    tenant_id: str
    session_id: str
    sequence: int
    state: Mapping[str, Any]
    created_at: float


class TenantStateStore:
    """In-memory durable-store contract with strict tenant filtering."""

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.time
        self._memory: dict[str, list[MemoryRecord]] = {}
        self._checkpoints: dict[tuple[str, str], list[CheckpointRecord]] = {}
        self._run_states: dict[tuple[str, str], LifecycleState] = {}
        self._lock = RLock()

    def append_memory(
        self,
        tenant_id: str,
        session_id: str,
        role: str,
        content: str,
    ) -> MemoryRecord:
        if not all(value.strip() for value in (tenant_id, session_id, role, content)):
            raise ValueError("memory fields cannot be empty")
        digest = hashlib.sha256(
            f"{tenant_id}:{session_id}:{role}:{content}:{self._clock()}".encode()
        ).hexdigest()[:16]
        record = MemoryRecord(
            digest,
            tenant_id,
            session_id,
            role,
            content,
            round(self._clock(), 6),
        )
        with self._lock:
            self._memory.setdefault(tenant_id, []).append(record)
        return record

    def recent(
        self,
        tenant_id: str,
        *,
        session_id: str | None = None,
        query: str = "",
        limit: int = 8,
    ) -> tuple[MemoryRecord, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        terms = {term for term in query.casefold().split() if len(term) > 2}
        with self._lock:
            candidates = list(self._memory.get(tenant_id, ()))
        if session_id:
            candidates = [item for item in candidates if item.session_id == session_id]
        if terms:
            candidates.sort(
                key=lambda item: (
                    sum(term in item.content.casefold() for term in terms),
                    item.created_at,
                ),
                reverse=True,
            )
        else:
            candidates.sort(key=lambda item: item.created_at, reverse=True)
        return tuple(candidates[:limit])

    def save_checkpoint(
        self,
        run_id: str,
        tenant_id: str,
        session_id: str,
        state: Mapping[str, Any],
    ) -> CheckpointRecord:
        safe_state = json.loads(json.dumps(dict(state), sort_keys=True))
        key = (tenant_id, run_id)
        with self._lock:
            history = self._checkpoints.setdefault(key, [])
            record = CheckpointRecord(
                run_id,
                tenant_id,
                session_id,
                len(history) + 1,
                safe_state,
                round(self._clock(), 6),
            )
            history.append(record)
            return record

    def latest_checkpoint(self, run_id: str, tenant_id: str) -> CheckpointRecord | None:
        with self._lock:
            history = self._checkpoints.get((tenant_id, run_id), ())
            return history[-1] if history else None

    def transition(
        self,
        run_id: str,
        tenant_id: str,
        state: LifecycleState,
    ) -> LifecycleState:
        key = (tenant_id, run_id)
        with self._lock:
            previous = self._run_states.get(key)
            if previous in TERMINAL_STATES:
                raise InvalidTransition(f"run already terminal: {previous.value}")
            if previous is state:
                raise InvalidTransition(f"duplicate transition: {state.value}")
            self._run_states[key] = state
            return state

    def state(self, run_id: str, tenant_id: str) -> LifecycleState | None:
        with self._lock:
            return self._run_states.get((tenant_id, run_id))


class ArtifactStore:
    """Content-addressed immutable artifacts with tenant ownership checks."""

    def __init__(self) -> None:
        self._content: dict[str, bytes] = {}
        self._refs: dict[str, ArtifactRef] = {}
        self._lock = RLock()

    def put(
        self,
        tenant_id: str,
        logical_name: str,
        content: bytes,
        media_type: str = "application/octet-stream",
    ) -> ArtifactRef:
        if not tenant_id.strip() or not logical_name.strip():
            raise ValueError("tenant_id and logical_name cannot be empty")
        digest = hashlib.sha256(content).hexdigest()
        artifact_id = hashlib.sha256(
            f"{tenant_id}:{logical_name}:{digest}".encode()
        ).hexdigest()[:20]
        ref = ArtifactRef(
            artifact_id,
            tenant_id,
            logical_name,
            media_type,
            len(content),
            digest,
        )
        with self._lock:
            existing = self._refs.get(artifact_id)
            if existing and existing != ref:
                raise RuntimeError("artifact identifier collision")
            self._refs[artifact_id] = ref
            self._content[artifact_id] = bytes(content)
        return ref

    def get(self, artifact_id: str, tenant_id: str) -> tuple[ArtifactRef, bytes]:
        with self._lock:
            ref = self._refs.get(artifact_id)
            if ref is None:
                raise KeyError("unknown artifact")
            if ref.tenant_id != tenant_id:
                raise TenantBoundaryError("artifact belongs to another tenant")
            return ref, bytes(self._content[artifact_id])

    def list_for_tenant(self, tenant_id: str) -> tuple[ArtifactRef, ...]:
        with self._lock:
            return tuple(ref for ref in self._refs.values() if ref.tenant_id == tenant_id)
