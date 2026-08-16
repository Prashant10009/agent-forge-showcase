"""Deterministic runtime adapters with scripted success and failure behavior."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import RLock
from typing import Callable, Iterable

from .contracts import RuntimeProfile, WorkRequest
from .control import CancellationToken


class RuntimeFailure(RuntimeError):
    retryable = False


class TransientRuntimeFailure(RuntimeFailure):
    retryable = True


class PermanentRuntimeFailure(RuntimeFailure):
    retryable = False


@dataclass(frozen=True, slots=True)
class AdapterResponse:
    output: str
    units: int
    cost: float
    duration_ms: float


class RuntimeAdapter:
    profile: RuntimeProfile

    def execute(self, request: WorkRequest, token: CancellationToken) -> AdapterResponse:
        raise NotImplementedError


class ScriptedAdapter(RuntimeAdapter):
    """Offline adapter whose behavior queue makes resilience tests reproducible."""

    def __init__(
        self,
        profile: RuntimeProfile,
        behaviors: Iterable[str] = ("success",),
        handler: Callable[[WorkRequest], str] | None = None,
    ) -> None:
        self.profile = profile
        self._behaviors = deque(behaviors)
        self._last_behavior = "success"
        self._handler = handler or self._default_handler
        self._lock = RLock()

    def execute(self, request: WorkRequest, token: CancellationToken) -> AdapterResponse:
        token.raise_if_cancelled()
        with self._lock:
            if self._behaviors:
                self._last_behavior = self._behaviors.popleft()
            behavior = self._last_behavior
        if behavior == "transient_error":
            raise TransientRuntimeFailure(f"transient failure from {self.profile.name}")
        if behavior == "permanent_error":
            raise PermanentRuntimeFailure(f"permanent failure from {self.profile.name}")
        if behavior == "cancel":
            token.cancel(f"{self.profile.name} observed operator cancellation")
            token.raise_if_cancelled()
        if behavior != "success":
            raise ValueError(f"unknown scripted behavior: {behavior}")
        output = self._handler(request)
        token.raise_if_cancelled()
        units = max(1, len(request.instruction.split()))
        return AdapterResponse(
            output=output,
            units=units,
            cost=self.profile.unit_cost,
            duration_ms=float(self.profile.latency_ms),
        )

    def _default_handler(self, request: WorkRequest) -> str:
        return (
            f"{self.profile.name} produced a verified public simulation for "
            f"{request.identity.run_id}: {request.instruction}"
        )


class AdapterRegistry:
    def __init__(self, adapters: Iterable[RuntimeAdapter] = ()) -> None:
        self._adapters: dict[str, RuntimeAdapter] = {}
        self._lock = RLock()
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: RuntimeAdapter, *, replace: bool = False) -> None:
        with self._lock:
            name = adapter.profile.name
            if name in self._adapters and not replace:
                raise ValueError(f"runtime already registered: {name}")
            self._adapters[name] = adapter

    def get(self, runtime_name: str) -> RuntimeAdapter:
        with self._lock:
            adapter = self._adapters.get(runtime_name)
        if adapter is None:
            raise KeyError(f"unknown runtime: {runtime_name}")
        return adapter

    def profiles(self) -> tuple[RuntimeProfile, ...]:
        with self._lock:
            return tuple(adapter.profile for adapter in self._adapters.values())
