"""Replaceable runtime adapters for the offline public core."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from threading import RLock

from .models import ExecutionResult, RuntimeDescriptor, TaskSpec


class RuntimeAdapter(ABC):
    descriptor: RuntimeDescriptor

    @abstractmethod
    def execute(self, task: TaskSpec) -> ExecutionResult:
        """Execute a task without assuming a specific model provider."""


class DeterministicAdapter(RuntimeAdapter):
    """Offline adapter that makes routing and orchestration reproducible."""

    def __init__(
        self,
        descriptor: RuntimeDescriptor,
        handler: Callable[[TaskSpec], str] | None = None,
    ) -> None:
        self.descriptor = descriptor
        self._handler = handler or self._default_handler

    def execute(self, task: TaskSpec) -> ExecutionResult:
        started = time.perf_counter()
        output = self._handler(task)
        duration_ms = (time.perf_counter() - started) * 1_000
        return ExecutionResult(task.task_id, self.descriptor.name, output, duration_ms)

    def _default_handler(self, task: TaskSpec) -> str:
        required = ", ".join(capability.value for capability in task.required)
        return f"{self.descriptor.name} completed {task.task_id} [{required}]: {task.instruction}"


class RuntimeRegistry:
    """Thread-safe adapter registry with explicit replacement semantics."""

    def __init__(self, adapters: Iterable[RuntimeAdapter] = ()) -> None:
        self._adapters: dict[str, RuntimeAdapter] = {}
        self._lock = RLock()
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: RuntimeAdapter, *, replace: bool = False) -> None:
        with self._lock:
            name = adapter.descriptor.name
            if name in self._adapters and not replace:
                raise ValueError(f"runtime already registered: {name}")
            self._adapters[name] = adapter

    def descriptors(self) -> tuple[RuntimeDescriptor, ...]:
        with self._lock:
            return tuple(adapter.descriptor for adapter in self._adapters.values())

    def execute(self, runtime_name: str, task: TaskSpec) -> ExecutionResult:
        with self._lock:
            adapter = self._adapters.get(runtime_name)
        if adapter is None:
            raise KeyError(f"unknown runtime: {runtime_name}")
        return adapter.execute(task)


def default_registry() -> RuntimeRegistry:
    """Build a provider-neutral registry suitable for demos and tests."""

    from .models import Capability

    return RuntimeRegistry(
        (
            DeterministicAdapter(
                RuntimeDescriptor(
                    "local-general",
                    frozenset({Capability.TEXT, Capability.REASONING}),
                    reliability=0.94,
                    latency_ms=80,
                    cost_tier=0,
                )
            ),
            DeterministicAdapter(
                RuntimeDescriptor(
                    "local-code",
                    frozenset({Capability.TEXT, Capability.CODE, Capability.TOOLS, Capability.DATA}),
                    reliability=0.91,
                    latency_ms=110,
                    cost_tier=1,
                )
            ),
            DeterministicAdapter(
                RuntimeDescriptor(
                    "local-vision",
                    frozenset({Capability.TEXT, Capability.VISION, Capability.REASONING}),
                    reliability=0.88,
                    latency_ms=140,
                    cost_tier=1,
                )
            ),
        )
    )
