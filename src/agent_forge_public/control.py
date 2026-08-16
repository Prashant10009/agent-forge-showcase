"""Operational control primitives: cancellation, circuits, budgets, and evidence."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Event, RLock
from typing import Callable, Iterator

from .contracts import CircuitState


class RunCancelled(RuntimeError):
    pass


class DeadlineExceeded(RunCancelled):
    pass


class BudgetExceeded(RuntimeError):
    pass


class CapacityExceeded(RuntimeError):
    pass


class CancellationToken:
    """Cooperative cancellation plus a wall-clock deadline envelope."""

    def __init__(
        self,
        timeout_ms: int,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        self._clock = clock or time.monotonic
        self._started = self._clock()
        self._deadline = self._started + timeout_ms / 1_000
        self._cancelled = Event()
        self._reason = ""
        self._lock = RLock()

    def cancel(self, reason: str = "cancelled by operator") -> None:
        with self._lock:
            self._reason = reason
            self._cancelled.set()

    @property
    def remaining_ms(self) -> int:
        return max(0, int((self._deadline - self._clock()) * 1_000))

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set() or self._clock() >= self._deadline

    def raise_if_cancelled(self) -> None:
        if self._cancelled.is_set():
            raise RunCancelled(self._reason or "cancelled")
        if self._clock() >= self._deadline:
            raise DeadlineExceeded("run deadline exceeded")


@dataclass(slots=True)
class CircuitSnapshot:
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    opened_at: float = 0.0
    half_open_claimed: bool = False


class CircuitRegistry:
    """Tenant-scoped circuit breaker with a single half-open probe."""

    def __init__(
        self,
        failure_threshold: int = 2,
        recovery_seconds: float = 30.0,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if failure_threshold < 1 or recovery_seconds < 0:
            raise ValueError("invalid circuit policy")
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self._clock = clock or time.monotonic
        self._records: dict[tuple[str, str], CircuitSnapshot] = {}
        self._lock = RLock()

    def allow(self, tenant_id: str, runtime_name: str) -> bool:
        key = (tenant_id, runtime_name)
        with self._lock:
            record = self._records.setdefault(key, CircuitSnapshot())
            if record.state is CircuitState.CLOSED:
                return True
            if record.state is CircuitState.OPEN:
                if self._clock() - record.opened_at < self.recovery_seconds:
                    return False
                record.state = CircuitState.HALF_OPEN
                record.half_open_claimed = False
            if record.half_open_claimed:
                return False
            record.half_open_claimed = True
            return True

    def available(self, tenant_id: str, runtime_name: str) -> bool:
        """Read-only eligibility check; unlike allow(), this does not claim a probe."""

        with self._lock:
            record = self._records.setdefault((tenant_id, runtime_name), CircuitSnapshot())
            if record.state is CircuitState.CLOSED:
                return True
            if record.state is CircuitState.OPEN:
                return self._clock() - record.opened_at >= self.recovery_seconds
            return not record.half_open_claimed

    def record_success(self, tenant_id: str, runtime_name: str) -> None:
        with self._lock:
            self._records[(tenant_id, runtime_name)] = CircuitSnapshot()

    def record_failure(self, tenant_id: str, runtime_name: str) -> None:
        key = (tenant_id, runtime_name)
        with self._lock:
            record = self._records.setdefault(key, CircuitSnapshot())
            record.consecutive_failures += 1
            if (
                record.state is CircuitState.HALF_OPEN
                or record.consecutive_failures >= self.failure_threshold
            ):
                record.state = CircuitState.OPEN
                record.opened_at = self._clock()
                record.half_open_claimed = False

    def snapshot(self, tenant_id: str, runtime_name: str) -> CircuitSnapshot:
        with self._lock:
            record = self._records.setdefault((tenant_id, runtime_name), CircuitSnapshot())
            return CircuitSnapshot(
                state=record.state,
                consecutive_failures=record.consecutive_failures,
                opened_at=record.opened_at,
                half_open_claimed=record.half_open_claimed,
            )


@dataclass(slots=True)
class _Reservation:
    tenant_id: str
    reserved: float
    committed: float = 0.0


class BudgetLedger:
    """Atomically reserves estimated cost before dispatch and commits actual cost."""

    def __init__(self) -> None:
        self._spent: dict[str, float] = {}
        self._reservations: dict[str, _Reservation] = {}
        self._lock = RLock()

    def reserve(self, run_id: str, tenant_id: str, amount: float, limit: float) -> None:
        if amount < 0 or limit < 0:
            raise ValueError("budget values cannot be negative")
        with self._lock:
            if run_id in self._reservations:
                raise ValueError("run already has a reservation")
            reserved_elsewhere = sum(
                reservation.reserved
                for reservation in self._reservations.values()
                if reservation.tenant_id == tenant_id
            )
            projected = self._spent.get(tenant_id, 0.0) + reserved_elsewhere + amount
            if projected > limit:
                raise BudgetExceeded(
                    f"reservation {amount:.4f} exceeds tenant limit {limit:.4f}"
                )
            self._reservations[run_id] = _Reservation(tenant_id, amount)

    def commit(self, run_id: str, actual: float) -> float:
        if actual < 0:
            raise ValueError("actual cost cannot be negative")
        with self._lock:
            reservation = self._reservations.pop(run_id, None)
            if reservation is None:
                raise KeyError("unknown budget reservation")
            if actual > reservation.reserved:
                raise BudgetExceeded("actual cost exceeded reserved amount")
            self._spent[reservation.tenant_id] = (
                self._spent.get(reservation.tenant_id, 0.0) + actual
            )
            return reservation.reserved - actual

    def release(self, run_id: str) -> float:
        with self._lock:
            reservation = self._reservations.pop(run_id, None)
            return reservation.reserved if reservation else 0.0

    def spent(self, tenant_id: str) -> float:
        with self._lock:
            return self._spent.get(tenant_id, 0.0)


@dataclass(slots=True)
class OutcomeStats:
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    total_cost: float = 0.0

    @property
    def reliability(self) -> float:
        return (self.successes + 1) / (self.successes + self.failures + 2)

    @property
    def mean_latency_ms(self) -> float:
        count = self.successes + self.failures
        return self.total_latency_ms / count if count else 0.0


class OutcomeLedger:
    """Stores bounded outcome evidence by tenant and runtime."""

    def __init__(self) -> None:
        self._stats: dict[tuple[str, str], OutcomeStats] = {}
        self._lock = RLock()

    def record(
        self,
        tenant_id: str,
        runtime_name: str,
        *,
        success: bool,
        latency_ms: float,
        cost: float,
    ) -> None:
        with self._lock:
            stats = self._stats.setdefault((tenant_id, runtime_name), OutcomeStats())
            if success:
                stats.successes += 1
            else:
                stats.failures += 1
            stats.total_latency_ms += max(0.0, latency_ms)
            stats.total_cost += max(0.0, cost)

    def get(self, tenant_id: str, runtime_name: str) -> OutcomeStats:
        with self._lock:
            stats = self._stats.get((tenant_id, runtime_name), OutcomeStats())
            return OutcomeStats(
                stats.successes,
                stats.failures,
                stats.total_latency_ms,
                stats.total_cost,
            )


class CapacityRegistry:
    """Rejects dispatch that would exceed a runtime's declared concurrency."""

    def __init__(self) -> None:
        self._active: dict[str, int] = {}
        self._lock = RLock()

    @contextmanager
    def claim(self, runtime_name: str, limit: int) -> Iterator[None]:
        with self._lock:
            active = self._active.get(runtime_name, 0)
            if active >= limit:
                raise CapacityExceeded(f"runtime capacity exhausted: {runtime_name}")
            self._active[runtime_name] = active + 1
        try:
            yield
        finally:
            with self._lock:
                remaining = self._active.get(runtime_name, 1) - 1
                if remaining:
                    self._active[runtime_name] = remaining
                else:
                    self._active.pop(runtime_name, None)

    def active(self, runtime_name: str) -> int:
        with self._lock:
            return self._active.get(runtime_name, 0)
