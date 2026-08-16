import unittest

from agent_forge_public.adapters import AdapterRegistry, ScriptedAdapter
from agent_forge_public.contracts import (
    LifecycleState,
    RoutingPlan,
    RunIdentity,
    RuntimeHealth,
    RuntimeProfile,
    WorkRequest,
)
from agent_forge_public.control import BudgetLedger, CancellationToken, CapacityRegistry, CircuitRegistry, OutcomeLedger
from agent_forge_public.execution import ResilientExecutor
from agent_forge_public.models import ActionKind, Capability
from agent_forge_public.selection import EvidenceRouter, NoEligibleRuntime


def profile(name, *, health=RuntimeHealth.HEALTHY, reliability=0.9, cost=0.05, tools=False):
    return RuntimeProfile(
        name,
        frozenset({Capability.TEXT, Capability.REASONING}),
        health,
        reliability,
        100,
        cost,
        supports_tools=tools,
    )


def request(run="run", *, action=ActionKind.READ, budget=1.0, attempts=3):
    return WorkRequest(
        RunIdentity(run, "tenant", "session", "turn"),
        "analyze system behavior",
        required=(Capability.TEXT, Capability.REASONING),
        action=action,
        budget_limit=budget,
        max_attempts=attempts,
    )


class SelectionAndExecutionTests(unittest.TestCase):
    def setUp(self):
        self.circuits = CircuitRegistry()
        self.outcomes = OutcomeLedger()

    def test_missing_capability_is_ineligible_with_reason(self):
        router = EvidenceRouter(self.circuits, self.outcomes)
        incomplete = RuntimeProfile("text", frozenset({Capability.TEXT}))
        with self.assertRaisesRegex(NoEligibleRuntime, "missing capabilities"):
            router.plan(request(), (incomplete,))

    def test_unavailable_runtime_is_excluded(self):
        router = EvidenceRouter(self.circuits, self.outcomes)
        with self.assertRaisesRegex(NoEligibleRuntime, "runtime unavailable"):
            router.plan(request(), (profile("down", health=RuntimeHealth.UNAVAILABLE),))

    def test_open_tenant_circuit_is_excluded(self):
        circuits = CircuitRegistry(1, 999)
        circuits.record_failure("tenant", "primary")
        router = EvidenceRouter(circuits, self.outcomes)
        with self.assertRaisesRegex(NoEligibleRuntime, "tenant circuit open"):
            router.plan(request(), (profile("primary"),))

    def test_write_requires_tool_support(self):
        router = EvidenceRouter(self.circuits, self.outcomes)
        with self.assertRaisesRegex(NoEligibleRuntime, "tool execution unsupported"):
            router.plan(request(action=ActionKind.WRITE), (profile("read-only"),))

    def test_score_order_is_deterministic(self):
        router = EvidenceRouter(self.circuits, self.outcomes)
        plan = router.plan(request(), (profile("z"), profile("a")))
        self.assertEqual((plan.selected,) + plan.fallbacks, ("a", "z"))

    def test_outcome_evidence_changes_selection(self):
        for _ in range(8):
            self.outcomes.record("tenant", "observed", success=True, latency_ms=10, cost=0.01)
            self.outcomes.record("tenant", "declared", success=False, latency_ms=500, cost=0.2)
        router = EvidenceRouter(self.circuits, self.outcomes)
        plan = router.plan(
            request(),
            (profile("declared", reliability=0.99), profile("observed", reliability=0.85)),
        )
        self.assertEqual(plan.selected, "observed")

    def _executor(self, adapters, circuits=None, budgets=None):
        return ResilientExecutor(
            AdapterRegistry(adapters),
            circuits or self.circuits,
            budgets or BudgetLedger(),
            self.outcomes,
            CapacityRegistry(),
        )

    def test_transient_failure_falls_back(self):
        primary = ScriptedAdapter(profile("primary"), ("transient_error",))
        backup = ScriptedAdapter(profile("backup"), ("success",))
        executor = self._executor((primary, backup))
        plan = RoutingPlan("run", "primary", ("backup",), ())
        report = executor.execute(request(), plan, CancellationToken(1000))
        self.assertTrue(report.success)
        self.assertEqual(report.runtime_name, "backup")
        self.assertEqual(len(report.attempts), 2)

    def test_permanent_failure_stops_fallback(self):
        primary = ScriptedAdapter(profile("primary"), ("permanent_error",))
        backup = ScriptedAdapter(profile("backup"), ("success",))
        report = self._executor((primary, backup)).execute(
            request(), RoutingPlan("run", "primary", ("backup",), ()), CancellationToken(1000)
        )
        self.assertFalse(report.success)
        self.assertEqual(len(report.attempts), 1)

    def test_max_attempts_bounds_fallback_chain(self):
        adapters = tuple(
            ScriptedAdapter(profile(name), ("transient_error",))
            for name in ("one", "two", "three")
        )
        report = self._executor(adapters).execute(
            request(attempts=2),
            RoutingPlan("run", "one", ("two", "three"), ()),
            CancellationToken(1000),
        )
        self.assertEqual(len(report.attempts), 2)

    def test_success_commits_actual_cost(self):
        budgets = BudgetLedger()
        adapter = ScriptedAdapter(profile("worker", cost=0.2))
        report = self._executor((adapter,), budgets=budgets).execute(
            request(), RoutingPlan("run", "worker", (), ()), CancellationToken(1000)
        )
        self.assertEqual(report.spent, 0.2)
        self.assertEqual(budgets.spent("tenant"), 0.2)

    def test_cancelled_adapter_releases_budget(self):
        budgets = BudgetLedger()
        adapter = ScriptedAdapter(profile("worker", cost=0.2), ("cancel",))
        with self.assertRaises(Exception):
            self._executor((adapter,), budgets=budgets).execute(
                request(), RoutingPlan("run", "worker", (), ()), CancellationToken(1000)
            )
        self.assertEqual(budgets.spent("tenant"), 0.0)


if __name__ == "__main__":
    unittest.main()
