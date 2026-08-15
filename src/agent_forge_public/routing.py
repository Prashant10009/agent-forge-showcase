"""Inspectable capability-based routing with a deliberately public policy."""

from __future__ import annotations

from dataclasses import dataclass

from .models import RouteDecision, RuntimeDescriptor, TaskSpec


class NoCompatibleRuntime(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PublicRoutingPolicy:
    """Generic demonstration weights; these are not production policy."""

    required_match: float = 40.0
    preferred_match: float = 6.0
    reliability: float = 30.0
    latency: float = 15.0
    cost: float = 9.0
    latency_ceiling_ms: int = 1_000


class CapabilityRouter:
    def __init__(self, policy: PublicRoutingPolicy | None = None) -> None:
        self.policy = policy or PublicRoutingPolicy()

    def choose(self, task: TaskSpec, runtimes: tuple[RuntimeDescriptor, ...]) -> RouteDecision:
        considered: dict[str, str] = {}
        eligible: list[tuple[float, str, dict[str, float]]] = []

        for runtime in runtimes:
            if not runtime.available:
                considered[runtime.name] = "excluded: unavailable"
                continue
            missing = set(task.required) - runtime.capabilities
            if missing:
                labels = ",".join(sorted(capability.value for capability in missing))
                considered[runtime.name] = f"excluded: missing {labels}"
                continue

            components = self._score(task, runtime)
            total = round(sum(components.values()), 4)
            preferred = len(set(task.preferred) & runtime.capabilities)
            considered[runtime.name] = f"eligible: score={total:.4f}; preferred_matches={preferred}"
            eligible.append((total, runtime.name, components))

        if not eligible:
            raise NoCompatibleRuntime(f"no compatible runtime for task {task.task_id}")

        score, runtime_name, components = max(eligible, key=lambda item: (item[0], item[1]))
        return RouteDecision(task.task_id, runtime_name, score, components, considered)

    def _score(self, task: TaskSpec, runtime: RuntimeDescriptor) -> dict[str, float]:
        preferred_matches = len(set(task.preferred) & runtime.capabilities)
        preferred_total = max(1, len(set(task.preferred)))
        latency_ratio = min(runtime.latency_ms, self.policy.latency_ceiling_ms) / self.policy.latency_ceiling_ms
        cost_ratio = runtime.cost_tier / 5
        return {
            "required": self.policy.required_match,
            "preferred": self.policy.preferred_match * (preferred_matches / preferred_total),
            "reliability": self.policy.reliability * runtime.reliability,
            "latency": self.policy.latency * (1 - latency_ratio),
            "cost": self.policy.cost * (1 - cost_ratio),
        }
