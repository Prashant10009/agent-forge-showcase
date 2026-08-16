"""Bounded execution with fallback, circuits, capacity, budget, and evidence."""

from __future__ import annotations

from dataclasses import dataclass

from .adapters import AdapterRegistry, RuntimeFailure
from .contracts import AttemptRecord, RoutingPlan, WorkRequest
from .control import (
    BudgetLedger,
    CancellationToken,
    CapacityExceeded,
    CapacityRegistry,
    CircuitRegistry,
    OutcomeLedger,
)


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    success: bool
    output: str
    runtime_name: str
    attempts: tuple[AttemptRecord, ...]
    spent: float
    error: str = ""


class ResilientExecutor:
    def __init__(
        self,
        adapters: AdapterRegistry,
        circuits: CircuitRegistry,
        budgets: BudgetLedger,
        outcomes: OutcomeLedger,
        capacity: CapacityRegistry,
    ) -> None:
        self.adapters = adapters
        self.circuits = circuits
        self.budgets = budgets
        self.outcomes = outcomes
        self.capacity = capacity

    def execute(
        self,
        request: WorkRequest,
        plan: RoutingPlan,
        token: CancellationToken,
    ) -> ExecutionReport:
        names = (plan.selected,) + plan.fallbacks
        names = names[: request.max_attempts]
        estimate = sum(self.adapters.get(name).profile.unit_cost for name in names)
        limit = self.budgets.spent(request.identity.tenant_id) + request.budget_limit
        self.budgets.reserve(
            request.identity.run_id,
            request.identity.tenant_id,
            estimate,
            limit,
        )
        attempts: list[AttemptRecord] = []
        spent = 0.0
        last_error = ""
        try:
            for attempt_number, runtime_name in enumerate(names, start=1):
                token.raise_if_cancelled()
                adapter = self.adapters.get(runtime_name)
                if not self.circuits.allow(request.identity.tenant_id, runtime_name):
                    last_error = "circuit open"
                    attempts.append(
                        AttemptRecord(runtime_name, attempt_number, False, 0.0, 0.0, "circuit_open", True)
                    )
                    continue
                try:
                    with self.capacity.claim(runtime_name, adapter.profile.concurrency_limit):
                        response = adapter.execute(request, token)
                    spent += response.cost
                    self.circuits.record_success(request.identity.tenant_id, runtime_name)
                    self.outcomes.record(
                        request.identity.tenant_id,
                        runtime_name,
                        success=True,
                        latency_ms=response.duration_ms,
                        cost=response.cost,
                    )
                    attempts.append(
                        AttemptRecord(
                            runtime_name,
                            attempt_number,
                            True,
                            response.duration_ms,
                            response.cost,
                        )
                    )
                    self.budgets.commit(request.identity.run_id, spent)
                    return ExecutionReport(
                        True,
                        response.output,
                        runtime_name,
                        tuple(attempts),
                        spent,
                    )
                except (RuntimeFailure, CapacityExceeded) as error:
                    retryable = bool(getattr(error, "retryable", True))
                    last_error = str(error)
                    self.circuits.record_failure(request.identity.tenant_id, runtime_name)
                    self.outcomes.record(
                        request.identity.tenant_id,
                        runtime_name,
                        success=False,
                        latency_ms=0.0,
                        cost=0.0,
                    )
                    attempts.append(
                        AttemptRecord(
                            runtime_name,
                            attempt_number,
                            False,
                            0.0,
                            0.0,
                            type(error).__name__,
                            retryable,
                        )
                    )
                    if not retryable:
                        break
            self.budgets.commit(request.identity.run_id, spent)
            return ExecutionReport(False, "", "", tuple(attempts), spent, last_error or "all runtimes failed")
        except Exception:
            self.budgets.release(request.identity.run_id)
            raise
