"""Exact-action approval manifests with ownership, replay, and race protection."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from threading import RLock
from typing import Any, Callable, Iterable, Mapping

from .contracts import ActionRequest, ManifestState, RunIdentity


class ManifestError(RuntimeError):
    pass


class ManifestOwnershipError(ManifestError):
    pass


class ManifestActionMismatch(ManifestError):
    pass


class ManifestReplay(ManifestError):
    pass


def _action_payload(action: ActionRequest | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(action, ActionRequest):
        return {
            "tool": action.tool,
            "arguments": dict(action.arguments),
            "action": action.action.value,
            "risk": action.risk.value,
        }
    return json.loads(json.dumps(dict(action), sort_keys=True))


def canonical_actions(actions: Iterable[ActionRequest | Mapping[str, Any]]) -> str:
    payload = [_action_payload(action) for action in actions]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def action_fingerprint(actions: Iterable[ActionRequest | Mapping[str, Any]]) -> str:
    return hashlib.sha256(canonical_actions(actions).encode()).hexdigest()


@dataclass(slots=True)
class ActionManifest:
    manifest_id: str
    identity: RunIdentity
    actions: tuple[dict[str, Any], ...]
    fingerprint: str
    state: ManifestState = ManifestState.PENDING
    created_at: float = 0.0
    expires_at: float = 0.0
    claimed_at: float = 0.0
    completed_at: float = 0.0
    execution_success: bool | None = None
    rejection_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["identity"] = asdict(self.identity)
        return payload


class ManifestRegistry:
    """Server-side registry; callers may approve only the captured action list."""

    def __init__(
        self,
        ttl_seconds: float = 300.0,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.ttl_seconds = ttl_seconds
        self._clock = clock or time.time
        self._by_id: dict[str, ActionManifest] = {}
        self._scope_index: dict[tuple[str, str, str, str, str], str] = {}
        self._lock = RLock()

    def create_or_reuse(
        self,
        identity: RunIdentity,
        actions: Iterable[ActionRequest],
    ) -> tuple[ActionManifest, str]:
        captured = tuple(_action_payload(action) for action in actions)
        if not captured:
            raise ValueError("a manifest requires at least one action")
        fingerprint = action_fingerprint(captured)
        key = (
            identity.tenant_id,
            identity.session_id,
            identity.run_id,
            identity.approval_scope,
            fingerprint,
        )
        with self._lock:
            self._expire_locked()
            existing_id = self._scope_index.get(key)
            if existing_id:
                existing = self._by_id[existing_id]
                if existing.state in {
                    ManifestState.PENDING,
                    ManifestState.APPROVED,
                }:
                    return existing, "reused"
                return existing, "suppressed"
            now = self._clock()
            manifest_id = hashlib.sha256(
                f"{identity.run_id}:{identity.approval_scope}:{fingerprint}:{now}".encode()
            ).hexdigest()[:20]
            manifest = ActionManifest(
                manifest_id=manifest_id,
                identity=identity,
                actions=captured,
                fingerprint=fingerprint,
                created_at=now,
                expires_at=now + self.ttl_seconds,
            )
            self._by_id[manifest_id] = manifest
            self._scope_index[key] = manifest_id
            return manifest, "created"

    def approve(self, manifest_id: str, identity: RunIdentity) -> ActionManifest:
        with self._lock:
            manifest = self._require(manifest_id)
            self._verify_owner(manifest, identity)
            self._expire_one(manifest)
            if manifest.state is ManifestState.APPROVED:
                return manifest
            if manifest.state is not ManifestState.PENDING:
                raise ManifestReplay(f"manifest cannot be approved from {manifest.state.value}")
            manifest.state = ManifestState.APPROVED
            return manifest

    def reject(
        self,
        manifest_id: str,
        identity: RunIdentity,
        reason: str = "rejected by operator",
    ) -> ActionManifest:
        with self._lock:
            manifest = self._require(manifest_id)
            self._verify_owner(manifest, identity)
            self._expire_one(manifest)
            if manifest.state is ManifestState.REJECTED:
                return manifest
            if manifest.state not in {ManifestState.PENDING, ManifestState.APPROVED}:
                raise ManifestReplay(f"manifest cannot be rejected from {manifest.state.value}")
            manifest.state = ManifestState.REJECTED
            manifest.rejection_reason = reason
            return manifest

    def claim(
        self,
        manifest_id: str,
        identity: RunIdentity,
        supplied_actions: Iterable[ActionRequest | Mapping[str, Any]],
    ) -> ActionManifest:
        """Atomically move APPROVED to EXECUTING after exact payload validation."""

        with self._lock:
            manifest = self._require(manifest_id)
            self._verify_owner(manifest, identity)
            self._expire_one(manifest)
            supplied = canonical_actions(supplied_actions)
            captured = canonical_actions(manifest.actions)
            if supplied != captured:
                raise ManifestActionMismatch("supplied actions differ from captured actions")
            if manifest.state is not ManifestState.APPROVED:
                raise ManifestReplay(f"manifest is not claimable: {manifest.state.value}")
            manifest.state = ManifestState.EXECUTING
            manifest.claimed_at = self._clock()
            return manifest

    def complete(self, manifest_id: str, *, success: bool) -> ActionManifest:
        with self._lock:
            manifest = self._require(manifest_id)
            if manifest.state is not ManifestState.EXECUTING:
                raise ManifestReplay(f"manifest is not executing: {manifest.state.value}")
            manifest.state = ManifestState.COMPLETED
            manifest.completed_at = self._clock()
            manifest.execution_success = success
            return manifest

    def get(self, manifest_id: str, identity: RunIdentity) -> ActionManifest:
        with self._lock:
            manifest = self._require(manifest_id)
            self._verify_owner(manifest, identity)
            self._expire_one(manifest)
            return manifest

    def _require(self, manifest_id: str) -> ActionManifest:
        manifest = self._by_id.get(manifest_id)
        if manifest is None:
            raise KeyError("unknown manifest")
        return manifest

    @staticmethod
    def _verify_owner(manifest: ActionManifest, identity: RunIdentity) -> None:
        expected = manifest.identity
        if identity.tenant_id != expected.tenant_id:
            raise ManifestOwnershipError("wrong tenant")
        if identity.session_id != expected.session_id:
            raise ManifestOwnershipError("wrong session")
        if identity.approval_scope != expected.approval_scope:
            raise ManifestOwnershipError("wrong approval scope")
        if identity.run_id != expected.run_id:
            raise ManifestOwnershipError("wrong run")

    def _expire_one(self, manifest: ActionManifest) -> None:
        if (
            manifest.state in {ManifestState.PENDING, ManifestState.APPROVED}
            and self._clock() >= manifest.expires_at
        ):
            manifest.state = ManifestState.EXPIRED

    def _expire_locked(self) -> None:
        for manifest in self._by_id.values():
            self._expire_one(manifest)
