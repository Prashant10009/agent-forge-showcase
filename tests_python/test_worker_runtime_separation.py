from __future__ import annotations

import unittest

from agent_forge_public.control import CircuitRegistry, OutcomeLedger
from agent_forge_public.control_plane import PublicControlPlane
from agent_forge_public.contracts import RuntimeHealth, RuntimeProfile
from agent_forge_public.models import ActionKind, Capability
from agent_forge_public.routing_explain import explain_plan
from agent_forge_public.selection import EvidenceRouter
from agent_forge_public.system_topology import ComponentLayer, VERIFIED_PUBLIC_TOPOLOGY
from agent_forge_public.worker_templates import (
    WorkerKind,
    apply_worker_template,
    describe_worker,
)


class WorkerRuntimeSeparationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plane = PublicControlPlane()
        self.tenant_id = "worker-test-tenant"
        self.profiles = (
            RuntimeProfile(
                "coding-runtime-a",
                frozenset({Capability.TEXT, Capability.CODE, Capability.REASONING}),
                RuntimeHealth.HEALTHY,
                reliability=0.95,
                latency_ms=100,
                unit_cost=0.20,
            ),
            RuntimeProfile(
                "coding-runtime-b",
                frozenset({Capability.TEXT, Capability.CODE, Capability.REASONING}),
                RuntimeHealth.HEALTHY,
                reliability=0.90,
                latency_ms=120,
                unit_cost=0.15,
            ),
            RuntimeProfile(
                "research-runtime-c",
                frozenset({Capability.TEXT, Capability.REASONING, Capability.DATA}),
                RuntimeHealth.HEALTHY,
                reliability=0.97,
                latency_ms=180,
                unit_cost=0.18,
            ),
        )

    def coding_request(self, run_id: str):
        base = self.plane.request(
            "Implement a parser change",
            run_id=run_id,
            tenant_id=self.tenant_id,
            action=ActionKind.READ,
        )
        return base, apply_worker_template(base, WorkerKind.CODING)

    def test_control_subsystems_are_not_generic_workers(self) -> None:
        control_names = {
            component.name
            for component in VERIFIED_PUBLIC_TOPOLOGY
            if component.layer
            in {
                ComponentLayer.CONTROL,
                ComponentLayer.DELIBERATION,
                ComponentLayer.VALIDATION,
                ComponentLayer.INTELLIGENCE,
                ComponentLayer.RUNTIME_STATE,
            }
        }
        self.assertEqual(
            control_names,
            {"Orchestrator", "Trimurti", "Sentinel gates", "Karma", "RTA"},
        )
        for component in VERIFIED_PUBLIC_TOPOLOGY:
            if component.name in control_names:
                self.assertFalse(component.generic_worker)

    def test_worker_template_adds_requirements_without_binding_runtime(self) -> None:
        base, request = self.coding_request("worker-contract")
        self.assertNotIn("specialist_worker", base.metadata)
        self.assertEqual(request.metadata["specialist_worker"], "coding")
        self.assertIn(Capability.CODE, request.required)
        self.assertFalse(describe_worker(WorkerKind.CODING)["runtime_bound"])
        self.assertFalse(describe_worker(WorkerKind.CODING)["control_plane_component"])

    def test_worker_requirements_exclude_incompatible_runtime(self) -> None:
        _, request = self.coding_request("worker-exclusion")
        router = EvidenceRouter(CircuitRegistry(), OutcomeLedger())
        plan = router.plan(request, self.profiles)
        explanation = explain_plan(plan, worker=WorkerKind.CODING)
        excluded = {item["runtime"]: item for item in explanation["excluded"]}
        self.assertIn("research-runtime-c", excluded)
        self.assertTrue(
            any(
                "missing capabilities" in reason
                for reason in excluded["research-runtime-c"]["reasons"]
            )
        )

    def test_synthetic_evidence_can_change_runtime_not_worker(self) -> None:
        outcomes = OutcomeLedger()
        router = EvidenceRouter(CircuitRegistry(), outcomes)
        _, before_request = self.coding_request("learning-before")
        before = router.plan(before_request, self.profiles)
        self.assertEqual(before.selected, "coding-runtime-a")

        for _ in range(6):
            outcomes.record(
                self.tenant_id,
                "coding-runtime-a",
                success=False,
                latency_ms=600,
                cost=0.20,
            )
            outcomes.record(
                self.tenant_id,
                "coding-runtime-b",
                success=True,
                latency_ms=120,
                cost=0.15,
            )

        _, after_request = self.coding_request("learning-after")
        after = router.plan(after_request, self.profiles)
        self.assertEqual(after.selected, "coding-runtime-b")
        self.assertEqual(before_request.metadata["specialist_worker"], "coding")
        self.assertEqual(after_request.metadata["specialist_worker"], "coding")
        self.assertNotEqual(before.selected, after.selected)


if __name__ == "__main__":
    unittest.main()
