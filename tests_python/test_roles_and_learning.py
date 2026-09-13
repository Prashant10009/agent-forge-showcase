from __future__ import annotations

import unittest

from agent_forge_public.control import CircuitRegistry, OutcomeLedger
from agent_forge_public.control_plane import PublicControlPlane
from agent_forge_public.contracts import RuntimeHealth, RuntimeProfile
from agent_forge_public.models import ActionKind, Capability
from agent_forge_public.roles import AgentRole, apply_role, describe_role
from agent_forge_public.routing_explain import explain_plan
from agent_forge_public.selection import EvidenceRouter


class RoleAndLearningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plane = PublicControlPlane()
        self.tenant_id = "role-test-tenant"
        self.profiles = (
            RuntimeProfile(
                "coding-specialist-a",
                frozenset({Capability.TEXT, Capability.CODE, Capability.REASONING}),
                RuntimeHealth.HEALTHY,
                reliability=0.95,
                latency_ms=100,
                unit_cost=0.20,
            ),
            RuntimeProfile(
                "coding-specialist-b",
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
        return base, apply_role(base, AgentRole.CODING)

    def test_role_adds_requirements_without_binding_runtime(self) -> None:
        base, request = self.coding_request("role-contract")
        self.assertNotIn("agent_role", base.metadata)
        self.assertEqual(request.metadata["agent_role"], "coding")
        self.assertIn(Capability.CODE, request.required)
        self.assertIn(Capability.TEXT, request.required)
        self.assertFalse(describe_role(AgentRole.CODING)["runtime_bound"])

    def test_role_requirements_exclude_incompatible_runtime(self) -> None:
        _, request = self.coding_request("role-exclusion")
        router = EvidenceRouter(CircuitRegistry(), OutcomeLedger())
        plan = router.plan(request, self.profiles)
        explanation = explain_plan(plan, role=AgentRole.CODING)
        excluded = {item["runtime"]: item for item in explanation["excluded"]}
        self.assertIn("research-runtime-c", excluded)
        self.assertTrue(
            any("missing capabilities" in reason for reason in excluded["research-runtime-c"]["reasons"])
        )

    def test_synthetic_outcome_evidence_can_change_runtime_not_role(self) -> None:
        outcomes = OutcomeLedger()
        router = EvidenceRouter(CircuitRegistry(), outcomes)
        _, before_request = self.coding_request("learning-before")
        before = router.plan(before_request, self.profiles)
        self.assertEqual(before.selected, "coding-specialist-a")

        for _ in range(6):
            outcomes.record(
                self.tenant_id,
                "coding-specialist-a",
                success=False,
                latency_ms=600,
                cost=0.20,
            )
            outcomes.record(
                self.tenant_id,
                "coding-specialist-b",
                success=True,
                latency_ms=120,
                cost=0.15,
            )

        _, after_request = self.coding_request("learning-after")
        after = router.plan(after_request, self.profiles)
        self.assertEqual(after.selected, "coding-specialist-b")
        self.assertEqual(before_request.metadata["agent_role"], "coding")
        self.assertEqual(after_request.metadata["agent_role"], "coding")
        self.assertNotEqual(before.selected, after.selected)


if __name__ == "__main__":
    unittest.main()
