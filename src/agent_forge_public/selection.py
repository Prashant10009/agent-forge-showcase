"""Evidence-aware runtime selection with explicit exclusion reasons."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    CandidateScore,
    RoutingPlan,
    RuntimeHealth,
    RuntimeProfile,
    WorkRequest,
)
from .control import CircuitRegistry, OutcomeLedger


class NoEligibleRuntime(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PublicSelectionPolicy:
    """Documented demonstration weights. These are not production policy."""

    capability: float = 35.0
    preference: float = 5.0
    declared_reliability: float = 15.0
    observed_reliability: float = 20.0
    health: float = 10.0
    latency: float = 8.0
    cost: float = 7.0
    latency_ceiling_ms: int = 1_000
    cost_ceiling: float = 1.0


class EvidenceRouter:
    def __init__(
        self,
        circuits: CircuitRegistry,
        outcomes: OutcomeLedger,
        policy: PublicSelectionPolicy | None = None,
    ) -> None:
        self.circuits = circuits
        self.outcomes = outcomes
        self.policy = policy or PublicSelectionPolicy()

    def plan(
        self,
        request: WorkRequest,
        profiles: tuple[RuntimeProfile, ...],
    ) -> RoutingPlan:
        candidates = tuple(self._score(request, profile) for profile in profiles)
        eligible = sorted(
            (candidate for candidate in candidates if candidate.eligible),
            key=lambda candidate: (-candidate.total, candidate.runtime_name),
        )
        if not eligible:
            reasons = "; ".join(
                f"{candidate.runtime_name}: {', '.join(candidate.reasons)}"
                for candidate in candidates
            )
            raise NoEligibleRuntime(f"no eligible runtime ({reasons})")
        return RoutingPlan(
            run_id=request.identity.run_id,
            selected=eligible[0].runtime_name,
            fallbacks=tuple(candidate.runtime_name for candidate in eligible[1:]),
            candidates=candidates,
        )

    def _score(self, request: WorkRequest, profile: RuntimeProfile) -> CandidateScore:
        reasons: list[str] = []
        missing = set(request.required) - profile.capabilities
        if missing:
            reasons.append(
                "missing capabilities: "
                + ",".join(sorted(capability.value for capability in missing))
            )
        if profile.health is RuntimeHealth.UNAVAILABLE:
            reasons.append("runtime unavailable")
        if not self.circuits.available(request.identity.tenant_id, profile.name):
            reasons.append("tenant circuit open")
        if request.action.value in {"write", "execute", "network"} and not profile.supports_tools:
            reasons.append("tool execution unsupported")
        if reasons:
            return CandidateScore(profile.name, False, 0.0, {}, tuple(reasons))

        preferred = len(set(request.preferred) & profile.capabilities)
        preferred_total = max(1, len(set(request.preferred)))
        observed = self.outcomes.get(request.identity.tenant_id, profile.name)
        health_factor = 1.0 if profile.health is RuntimeHealth.HEALTHY else 0.5
        latency_ratio = min(profile.latency_ms, self.policy.latency_ceiling_ms) / self.policy.latency_ceiling_ms
        cost_ratio = min(profile.unit_cost, self.policy.cost_ceiling) / self.policy.cost_ceiling
        components = {
            "capability": self.policy.capability,
            "preference": self.policy.preference * preferred / preferred_total,
            "declared_reliability": self.policy.declared_reliability * profile.reliability,
            "observed_reliability": self.policy.observed_reliability * observed.reliability,
            "health": self.policy.health * health_factor,
            "latency": self.policy.latency * (1 - latency_ratio),
            "cost": self.policy.cost * (1 - cost_ratio),
        }
        return CandidateScore(
            profile.name,
            True,
            round(sum(components.values()), 4),
            components,
            ("eligible",),
        )
