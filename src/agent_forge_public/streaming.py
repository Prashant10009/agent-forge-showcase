"""Deterministic stream lifecycle contracts used by the public simulation."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Callable, Mapping


class StreamEventKind(str, Enum):
    DELTA = "delta"
    HEARTBEAT = "heartbeat"
    DONE = "done"
    INCOMPLETE = "incomplete"
    ERROR = "error"
    CANCELLED = "cancelled"


TERMINAL_STREAM_KINDS = frozenset(
    {
        StreamEventKind.DONE,
        StreamEventKind.INCOMPLETE,
        StreamEventKind.ERROR,
        StreamEventKind.CANCELLED,
    }
)


class StreamContractError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class StreamEvent:
    sequence: int
    timestamp: float
    kind: StreamEventKind
    text: str = ""
    finish_reason: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        return payload


class StreamLifecycle:
    """Append-only stream journal with partial-preserving inactivity closure."""

    def __init__(
        self,
        inactivity_ms: int,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if inactivity_ms <= 0:
            raise ValueError("inactivity_ms must be positive")
        self._clock = clock or time.monotonic
        self._inactivity_seconds = inactivity_ms / 1_000
        self._last_activity = self._clock()
        self._events: list[StreamEvent] = []
        self._partial: list[str] = []
        self._terminal: StreamEvent | None = None
        self._lock = RLock()

    def delta(self, text: str) -> StreamEvent:
        if not text:
            raise ValueError("delta text cannot be empty")
        with self._lock:
            event = self._append(StreamEventKind.DELTA, text=text)
            self._partial.append(text)
            self._last_activity = self._clock()
            return event

    def heartbeat(self) -> StreamEvent:
        with self._lock:
            event = self._append(StreamEventKind.HEARTBEAT)
            self._last_activity = self._clock()
            return event

    def finish(
        self,
        kind: StreamEventKind = StreamEventKind.DONE,
        *,
        text: str | None = None,
        reason: str = "",
        details: Mapping[str, Any] | None = None,
    ) -> StreamEvent:
        if kind not in TERMINAL_STREAM_KINDS:
            raise ValueError("finish requires a terminal stream kind")
        with self._lock:
            final_text = "".join(self._partial) if text is None else text
            event = self._append(kind, text=final_text, reason=reason, details=details)
            self._terminal = event
            return event

    def close_if_inactive(self) -> StreamEvent | None:
        """Close a stalled stream, preserving visible partial output when present."""

        with self._lock:
            if self._terminal is not None:
                return self._terminal
            if self._clock() - self._last_activity < self._inactivity_seconds:
                return None
            if self._partial:
                return self.finish(
                    StreamEventKind.DONE,
                    reason="inactivity_cutoff",
                    details={"partial_preserved": True},
                )
            return self.finish(
                StreamEventKind.INCOMPLETE,
                reason="inactivity_cutoff",
                details={"partial_preserved": False},
            )

    def require_terminal(self) -> StreamEvent:
        with self._lock:
            if self._terminal is None:
                raise StreamContractError("stream ended without a terminal event")
            return self._terminal

    def snapshot(self) -> tuple[StreamEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def _append(
        self,
        kind: StreamEventKind,
        *,
        text: str = "",
        reason: str = "",
        details: Mapping[str, Any] | None = None,
    ) -> StreamEvent:
        if self._terminal is not None:
            raise StreamContractError(
                f"stream already terminated as {self._terminal.kind.value}"
            )
        event = StreamEvent(
            len(self._events) + 1,
            round(self._clock(), 6),
            kind,
            text,
            reason,
            dict(details or {}),
        )
        self._events.append(event)
        return event
