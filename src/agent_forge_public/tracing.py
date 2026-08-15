"""Small, inspectable trace recorder with deterministic sequence numbers."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from threading import RLock
from typing import Any


class TraceRecorder:
    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.time
        self._events: list[dict[str, Any]] = []
        self._lock = RLock()

    def emit(self, stage: str, state: str, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            event = {
                "sequence": len(self._events) + 1,
                "timestamp": round(self._clock(), 6),
                "stage": stage,
                "state": state,
                "details": dict(details or {}),
            }
            self._events.append(event)
            return dict(event)

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            return tuple(dict(event) for event in self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
