"""Rich public contracts for a governed, event-driven orchestration run.

These contracts are independently authored for the portfolio edition.  They
model the relationships a control plane must enforce without containing any
production provider, prompt, threshold, or persistence schema.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping

from .models import ActionKind, Capability


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LifecycleState(str, Enum):
    ACCEPTED = "accepted"
    CLASSIFIED = "classified"
    CONTEXT_READY = "context_ready"
    REVIEWED = "reviewed"
    ROUTED = "routed"
    APPROVAL_REQUIRED = "approval_required"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATES = frozenset(
    {LifecycleState.COMPLETED, LifecycleState.FAILED, LifecycleState.CANCELLED}
)


class RuntimeHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class ManifestState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class RunIdentity:
    run_id: str
    tenant_id: str
    session_id: str
    approval_scope: str

    def __post_init__(self) -> None:
        for name, value in (
            ("run_id", self.run_id),
            ("tenant_id", self.tenant_id),
            ("session_id", self.session_id),
            ("approval_scope", self.approval_scope),
        ):
            if not value.strip():
                raise ValueError(f"{name} cannot be empty")


@dataclass(frozen=True, slots=True)
class WorkRequest:
    identity: RunIdentity
    instruction: str
    required: tuple[Capability, ...] = (Capability.TEXT,)
    preferred: tuple[Capability, ...] = ()
    action: ActionKind = ActionKind.READ
    risk: RiskLevel = RiskLevel.LOW
    deadline_ms: int = 5_000
    max_attempts: int = 3
    budget_limit: float = 1.0
    expected_artifacts: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.instruction.strip():
            raise ValueError("instruction cannot be empty")
        if self.deadline_ms <= 0:
            raise ValueError("deadline_ms must be positive")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.budget_limit < 0:
            raise ValueError("budget_limit cannot be negative")


@dataclass(frozen=True, slots=True)
class RuntimeProfile:
    name: str
    capabilities: frozenset[Capability]
    health: RuntimeHealth = RuntimeHealth.HEALTHY
    reliability: float = 1.0
    latency_ms: int = 100
    unit_cost: float = 0.05
    concurrency_limit: int = 2
    supports_tools: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("runtime name cannot be empty")
        if not 0 <= self.reliability <= 1:
            raise ValueError("reliability must be between 0 and 1")
        if self.latency_ms < 0 or self.unit_cost < 0:
            raise ValueError("latency and cost cannot be negative")
        if self.concurrency_limit < 1:
            raise ValueError("concurrency_limit must be positive")


@dataclass(frozen=True, slots=True)
class CandidateScore:
    runtime_name: str
    eligible: bool
    total: float
    components: Mapping[str, float]
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RoutingPlan:
    run_id: str
    selected: str
    fallbacks: tuple[str, ...]
    candidates: tuple[CandidateScore, ...]
    policy_label: str = "public-demonstration-v2"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ActionRequest:
    tool: str
    arguments: Mapping[str, Any]
    action: ActionKind
    risk: RiskLevel

    def __post_init__(self) -> None:
        if not self.tool.strip():
            raise ValueError("tool cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionResult:
    tool: str
    success: bool
    summary: str
    artifact_ids: tuple[str, ...] = ()
    error: str = ""


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    runtime_name: str
    attempt: int
    success: bool
    duration_ms: float
    cost: float
    error_kind: str = ""
    retryable: bool = False


@dataclass(frozen=True, slots=True)
class RunResult:
    run_id: str
    state: LifecycleState
    output: str = ""
    runtime_name: str = ""
    attempts: tuple[AttemptRecord, ...] = ()
    actions: tuple[ActionResult, ...] = ()
    artifact_ids: tuple[str, ...] = ()
    verification: Mapping[str, bool] = field(default_factory=dict)
    error: str = ""
    spent: float = 0.0

    def __post_init__(self) -> None:
        if self.state not in TERMINAL_STATES:
            raise ValueError("RunResult requires a terminal state")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReviewFinding:
    perspective: str
    severity: RiskLevel
    message: str
    recommendation: str


@dataclass(frozen=True, slots=True)
class ReviewReport:
    required: bool
    findings: tuple[ReviewFinding, ...]
    approved_to_route: bool
    rationale: str


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    artifact_id: str
    tenant_id: str
    logical_name: str
    media_type: str
    size: int
    digest: str

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)
