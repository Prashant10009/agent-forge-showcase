"""Executable public proof that agent role and runtime identity are separate.

Run from the repository root:

    python examples/role_routing_learning_demo.py

The example is deterministic, offline, provider-neutral, and synthetic. It uses only
the public demonstration policy and does not reproduce production routing behavior.
"""

from __future__ import annotations

import json

from agent_forge_public.control import CircuitRegistry, OutcomeLedger
from agent_forge_public.control_plane import PublicControlPlane
from agent_forge_public.contracts import RuntimeHealth, RuntimeProfile
from agent_forge_public.models import ActionKind, Capability
from agent_forge_public.roles import AgentRole, apply_role, describe_role
from agent_forge_public.routing_explain import explain_plan
from agent_forge_public.selection import EvidenceRouter


def public_profiles() -> tuple[RuntimeProfile, ...]:
    return (
        RuntimeProfile(
            name="coding-specialist-a",
            capabilities=frozenset(
                {Capability.TEXT, Capability.CODE, Capability.REASONING}
            ),
            health=RuntimeHealth.HEALTHY,
            reliability=0.95,
            latency_ms=100,
            unit_cost=0.20,
        ),
        RuntimeProfile(
            name="coding-specialist-b",
            capabilities=frozenset(
                {Capability.TEXT, Capability.CODE, Capability.REASONING}
            ),
            health=RuntimeHealth.HEALTHY,
            reliability=0.90,
            latency_ms=120,
            unit_cost=0.15,
        ),
        RuntimeProfile(
            name="research-runtime-c",
            capabilities=frozenset(
                {Capability.TEXT, Capability.REASONING, Capability.DATA}
            ),
            health=RuntimeHealth.HEALTHY,
            reliability=0.97,
            latency_ms=180,
            unit_cost=0.18,
        ),
    )


def main() -> None:
    tenant_id = "public-learning-demo"
    plane = PublicControlPlane()
    outcomes = OutcomeLedger()
    router = EvidenceRouter(CircuitRegistry(), outcomes)

    base_request = plane.request(
        "Implement and verify a small parser change",
        run_id="role-demo-before",
        tenant_id=tenant_id,
        action=ActionKind.READ,
    )
    coding_request = apply_role(base_request, AgentRole.CODING)
    profiles = public_profiles()

    before = router.plan(coding_request, profiles)

    # Synthetic evidence only: repeated poor outcomes for A and strong outcomes for B.
    # This is deliberately obvious so the demonstration remains inspectable.
    for _ in range(6):
        outcomes.record(
            tenant_id,
            "coding-specialist-a",
            success=False,
            latency_ms=600,
            cost=0.20,
        )
        outcomes.record(
            tenant_id,
            "coding-specialist-b",
            success=True,
            latency_ms=120,
            cost=0.15,
        )

    after_request = apply_role(
        plane.request(
            "Implement and verify another small parser change",
            run_id="role-demo-after",
            tenant_id=tenant_id,
            action=ActionKind.READ,
        ),
        AgentRole.CODING,
    )
    after = router.plan(after_request, profiles)

    payload = {
        "synthetic": True,
        "production_policy": False,
        "thesis": "agent role remains stable while runtime selection can change",
        "role": describe_role(AgentRole.CODING),
        "before_evidence": explain_plan(before, role=AgentRole.CODING),
        "synthetic_evidence": {
            "coding-specialist-a": {"successes": 0, "failures": 6},
            "coding-specialist-b": {"successes": 6, "failures": 0},
        },
        "after_evidence": explain_plan(after, role=AgentRole.CODING),
        "role_unchanged": (
            coding_request.metadata["agent_role"]
            == after_request.metadata["agent_role"]
            == AgentRole.CODING.value
        ),
        "runtime_changed": before.selected != after.selected,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
