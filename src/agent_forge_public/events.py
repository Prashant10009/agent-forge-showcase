"""Lifecycle event journal with explicit terminal-state semantics."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from threading import RLock
from typing import Any, Callable, Mapping

from .contracts import LifecycleState, RunIdentity, TERMINAL_STATES


class TerminalEventError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    sequence: int
    timestamp: float
    run_id: str
    tenant_id: str
    session_id: str
    stage: str
    state: LifecycleState
    details: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        return payload


class EventJournal:
    """Thread-safe append-only journal that permits exactly one terminal event."""

    def __init__(self, identity: RunIdentity, clock: Callable[[], float] | None = None) -> None:
        self.identity = identity
        self._clock = clock or time.time
        self._events: list[LifecycleEvent] = []
        self._terminal: LifecycleEvent | None = None
        self._lock = RLock()

    def emit(
        self,
        stage: str,
        state: LifecycleState,
        details: Mapping[str, Any] | None = None,
    ) -> LifecycleEvent:
        with self._lock:
            if self._terminal is not None:
                raise TerminalEventError(
                    f"run already terminated as {self._terminal.state.value}"
                )
            event = LifecycleEvent(
                sequence=len(self._events) + 1,
                timestamp=round(self._clock(), 6),
                run_id=self.identity.run_id,
                tenant_id=self.identity.tenant_id,
                session_id=self.identity.session_id,
                stage=stage,
                state=state,
                details=dict(details or {}),
            )
            self._events.append(event)
            if state in TERMINAL_STATES:
                self._terminal = event
            return event

    @property
    def terminal(self) -> LifecycleEvent | None:
        with self._lock:
            return self._terminal

    def snapshot(self) -> tuple[LifecycleEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def public_snapshot(self) -> tuple[dict[str, Any], ...]:
        return tuple(event.to_dict() for event in self.snapshot())
