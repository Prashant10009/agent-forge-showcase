"""Executable public proof of configured-worker/runtime separation.

Run from the repository root:

    python examples/worker_runtime_learning_demo.py

The example is deterministic, offline, provider-neutral, and synthetic. It does not
reproduce production routing policy or imply that Agent Forge control subsystems are
instances of a generic worker class.
"""

from __future__ import annotations

import json

from agent_forge_public.control import CircuitRegistry, OutcomeLedger
from agent_forge_public.control_plane import PublicControlPlane
from agent_forge_public.contracts import RuntimeHealth, RuntimeProfile
from agent_forge_public.models import ActionKind, Capability
from agent_forge_public.routing_explain import explain_plan
from agent_forge_public.selection import EvidenceRouter
from agent_forge_public.system_topology import topology_snapshot
from agent_forge_public.worker_templates import (
    WorkerKind,
    apply_worker_template,
    describe_worker,
)


def public_profiles() -> tuple[RuntimeProfile, ...]:
    return (
        RuntimeProfile(
            name="coding-runtime-a",
            capabilities=frozenset({Capability.TEXT, Capability.CODE, Capability.REASONING}),
            health=RuntimeHealth.HEALTHY,
            reliability=0.95,
            latency_ms=100,
            unit_cost=0.20,
        ),
        RuntimeProfile(
            name="coding-runtime-b",
            capabilities=frozenset({Capability.TEXT, Capability.CODE, Capability.REASONING}),
            health=RuntimeHealth.HEALTHY,
            reliability=0.90,
            latency_ms=120,
            unit_cost=0.15,
        ),
        RuntimeProfile(
            name="research-runtime-c",
            capabilities=frozenset({Capability.TEXT, Capability.REASONING, Capability.DATA}),
            health=RuntimeHealth.HEALTHY,
            reliability=0.97,
            latency_ms=180,
            unit_cost=0.18,
        ),
    )


def main() -> None:
    tenant_id = "public-worker-demo"
    plane = PublicControlPlane()
    outcomes = OutcomeLedger()
    router = EvidenceRouter(CircuitRegistry(), outcomes)

    before_request = apply_worker_template(
        plane.request(
            "Implement and verify a small parser change",
            run_id="worker-demo-before",
            tenant_id=tenant_id,
            action=ActionKind.READ,
        ),
        WorkerKind.CODING,
    )
    profiles = public_profiles()
    before = router.plan(before_request, profiles)

    # Synthetic public evidence only. The values are intentionally exaggerated so
    # the routing change is deterministic and inspectable.
    for _ in range(6):
        outcomes.record(
            tenant_id,
            "coding-runtime-a",
            success=False,
            latency_ms=600,
            cost=0.20,
        )
        outcomes.record(
            tenant_id,
            "coding-runtime-b",
            success=True,
            latency_ms=120,
            cost=0.15,
        )

    after_request = apply_worker_template(
        plane.request(
            "Implement and verify another small parser change",
            run_id="worker-demo-after",
            tenant_id=tenant_id,
            action=ActionKind.READ,
        ),
        WorkerKind.CODING,
    )
    after = router.plan(after_request, profiles)

    payload = {
        "synthetic": True,
        "production_policy": False,
        "architecture_claim": (
            "control subsystems, configured specialist workers, and execution runtimes "
            "are separate layers"
        ),
        "topology": topology_snapshot(),
        "worker": describe_worker(WorkerKind.CODING),
        "before_evidence": explain_plan(before, worker=WorkerKind.CODING),
        "synthetic_evidence": {
            "coding-runtime-a": {"successes": 0, "failures": 6},
            "coding-runtime-b": {"successes": 6, "failures": 0},
        },
        "after_evidence": explain_plan(after, worker=WorkerKind.CODING),
        "worker_unchanged": (
            before_request.metadata["specialist_worker"]
            == after_request.metadata["specialist_worker"]
            == WorkerKind.CODING.value
        ),
        "runtime_changed": before.selected != after.selected,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
