import unittest

from agent_forge_public.contracts import CircuitState, LifecycleState, RunIdentity
from agent_forge_public.control import (
    BudgetExceeded,
    BudgetLedger,
    CancellationToken,
    CapacityExceeded,
    CapacityRegistry,
    CircuitRegistry,
    DeadlineExceeded,
    OutcomeLedger,
    RunCancelled,
)
from agent_forge_public.events import EventJournal, TerminalEventError


class MutableClock:
    def __init__(self, value=10.0):
        self.value = value

    def __call__(self):
        return self.value


class ControlPrimitiveTests(unittest.TestCase):
    def test_explicit_cancellation_preserves_reason(self):
        token = CancellationToken(1000)
        token.cancel("operator stop")
        with self.assertRaisesRegex(RunCancelled, "operator stop"):
            token.raise_if_cancelled()

    def test_deadline_is_checked_at_point_of_use(self):
        clock = MutableClock()
        token = CancellationToken(100, clock=clock)
        clock.value += 0.2
        with self.assertRaises(DeadlineExceeded):
            token.raise_if_cancelled()

    def test_budget_reservation_is_atomic_per_tenant(self):
        ledger = BudgetLedger()
        ledger.reserve("a", "tenant", 0.6, 1.0)
        with self.assertRaises(BudgetExceeded):
            ledger.reserve("b", "tenant", 0.5, 1.0)

    def test_budget_commit_charges_actual_not_reserved(self):
        ledger = BudgetLedger()
        ledger.reserve("a", "tenant", 0.8, 1.0)
        self.assertAlmostEqual(ledger.commit("a", "tenant", 0.25), 0.55)
        self.assertAlmostEqual(ledger.spent("tenant"), 0.25)

    def test_budget_release_does_not_charge(self):
        ledger = BudgetLedger()
        ledger.reserve("a", "tenant", 0.4, 1.0)
        self.assertEqual(ledger.release("a", "tenant"), 0.4)
        self.assertEqual(ledger.spent("tenant"), 0.0)

    def test_same_run_id_is_independent_across_tenants(self):
        ledger = BudgetLedger()
        ledger.reserve("shared", "tenant-a", 0.4, 1.0)
        ledger.reserve("shared", "tenant-b", 0.3, 1.0)
        ledger.commit("shared", "tenant-a", 0.2)
        ledger.commit("shared", "tenant-b", 0.1)
        self.assertAlmostEqual(ledger.spent("tenant-a"), 0.2)
        self.assertAlmostEqual(ledger.spent("tenant-b"), 0.1)

    def test_capacity_claim_is_released(self):
        capacity = CapacityRegistry()
        with capacity.claim("worker", 1):
            self.assertEqual(capacity.active("worker"), 1)
            with self.assertRaises(CapacityExceeded):
                with capacity.claim("worker", 1):
                    pass
        self.assertEqual(capacity.active("worker"), 0)

    def test_circuit_opens_after_threshold(self):
        clock = MutableClock()
        circuits = CircuitRegistry(2, 30, clock=clock)
        circuits.record_failure("tenant", "worker")
        self.assertTrue(circuits.allow("tenant", "worker"))
        circuits.record_failure("tenant", "worker")
        self.assertEqual(circuits.snapshot("tenant", "worker").state, CircuitState.OPEN)
        self.assertFalse(circuits.allow("tenant", "worker"))

    def test_half_open_allows_one_probe(self):
        clock = MutableClock()
        circuits = CircuitRegistry(1, 5, clock=clock)
        circuits.record_failure("tenant", "worker")
        clock.value += 6
        self.assertTrue(circuits.allow("tenant", "worker"))
        self.assertFalse(circuits.allow("tenant", "worker"))

    def test_circuit_is_tenant_scoped(self):
        circuits = CircuitRegistry(1, 30)
        circuits.record_failure("a", "worker")
        self.assertFalse(circuits.available("a", "worker"))
        self.assertTrue(circuits.available("b", "worker"))

    def test_outcomes_are_tenant_scoped_and_smoothed(self):
        outcomes = OutcomeLedger()
        outcomes.record("a", "worker", success=True, latency_ms=80, cost=0.1)
        self.assertGreater(outcomes.get("a", "worker").reliability, 0.5)
        self.assertEqual(outcomes.get("b", "worker").reliability, 0.5)

    def test_event_sequences_are_monotonic(self):
        journal = EventJournal(RunIdentity("r", "t", "s", "scope"), clock=lambda: 2.0)
        first = journal.emit("intake", LifecycleState.ACCEPTED)
        second = journal.emit("done", LifecycleState.COMPLETED)
        self.assertEqual((first.sequence, second.sequence), (1, 2))

    def test_no_event_after_terminal(self):
        journal = EventJournal(RunIdentity("r", "t", "s", "scope"))
        journal.emit("done", LifecycleState.FAILED)
        with self.assertRaises(TerminalEventError):
            journal.emit("late", LifecycleState.RUNNING)


if __name__ == "__main__":
    unittest.main()
