"""Runnable resilience scenarios for the public control-plane lab."""

from __future__ import annotations

from typing import Any

from .adapters import AdapterRegistry, ScriptedAdapter
from .contracts import RiskLevel, RuntimeHealth, RuntimeProfile
from .control_plane import PublicControlPlane
from .models import ActionKind, Capability


SCENARIOS = ("happy", "fallback", "governed", "rejected")


def run_scenario(name: str) -> dict[str, Any]:
    if name not in SCENARIOS:
        raise ValueError(f"unknown scenario: {name}")
    if name == "fallback":
        plane = PublicControlPlane(adapters=_fallback_registry())
        request = plane.request(
            "Analyze and explain a resilient architecture",
            run_id="fallback-run",
            max_attempts=2,
        )
        return plane.start(request).to_dict()

    plane = PublicControlPlane()
    if name == "happy":
        request = plane.request(
            "Analyze the public control-plane architecture",
            run_id="happy-run",
        )
        return plane.start(request).to_dict()

    request = plane.request(
        "Implement and verify a public architecture report",
        run_id=f"{name}-run",
        action=ActionKind.WRITE,
        risk=RiskLevel.HIGH,
        expected_artifacts=("architecture-report.txt",),
    )
    pending = plane.start(request)
    if pending.manifest is None:
        raise RuntimeError("governed scenario did not create a manifest")
    if name == "rejected":
        return plane.reject(
            pending.manifest.manifest_id,
            request.identity,
            "operator rejected the proposed write",
        ).to_dict()
    return plane.approve(pending.manifest.manifest_id, request.identity).to_dict()


def run_all_scenarios() -> dict[str, dict[str, Any]]:
    return {name: run_scenario(name) for name in SCENARIOS}


def _fallback_registry() -> AdapterRegistry:
    capabilities = frozenset({Capability.TEXT, Capability.REASONING})
    return AdapterRegistry(
        (
            ScriptedAdapter(
                RuntimeProfile(
                    "preferred-core",
                    capabilities,
                    RuntimeHealth.HEALTHY,
                    reliability=0.99,
                    latency_ms=20,
                    unit_cost=0.02,
                ),
                ("transient_error",),
            ),
            ScriptedAdapter(
                RuntimeProfile(
                    "recovery-core",
                    capabilities,
                    RuntimeHealth.DEGRADED,
                    reliability=0.80,
                    latency_ms=200,
                    unit_cost=0.03,
                ),
                ("success",),
            ),
        )
    )
