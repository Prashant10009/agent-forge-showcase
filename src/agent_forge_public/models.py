"""Public data contracts shared by routing, governance, and execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


class Capability(str, Enum):
    TEXT = "text"
    CODE = "code"
    REASONING = "reasoning"
    TOOLS = "tools"
    VISION = "vision"
    DATA = "data"


class ActionKind(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"


class RunStatus(str, Enum):
    APPROVAL_REQUIRED = "approval_required"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """A bounded unit of work with explicit capabilities and authority."""

    task_id: str
    instruction: str
    required: tuple[Capability, ...] = (Capability.TEXT,)
    preferred: tuple[Capability, ...] = ()
    action: ActionKind = ActionKind.READ
    depends_on: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id cannot be empty")
        if not self.instruction.strip():
            raise ValueError("instruction cannot be empty")
        if self.task_id in self.depends_on:
            raise ValueError("a task cannot depend on itself")


@dataclass(frozen=True, slots=True)
class RuntimeDescriptor:
    name: str
    capabilities: frozenset[Capability]
    reliability: float = 1.0
    latency_ms: int = 100
    cost_tier: int = 1
    available: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("runtime name cannot be empty")
        if not 0 <= self.reliability <= 1:
            raise ValueError("reliability must be between 0 and 1")
        if self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        if not 0 <= self.cost_tier <= 5:
            raise ValueError("cost_tier must be between 0 and 5")


@dataclass(frozen=True, slots=True)
class RouteDecision:
    task_id: str
    runtime_name: str
    score: float
    components: Mapping[str, float]
    considered: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    task_id: str
    runtime_name: str
    output: str
    duration_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    approval_id: str
    task_id: str
    action: ActionKind
    summary: str
    challenge: str = field(repr=False)

    def public_dict(self) -> dict[str, str]:
        return {
            "approval_id": self.approval_id,
            "task_id": self.task_id,
            "action": self.action.value,
            "summary": self.summary,
        }


@dataclass(frozen=True, slots=True)
class RunOutcome:
    status: RunStatus
    task_id: str
    route: RouteDecision
    result: ExecutionResult | None = None
    approval: ApprovalRequest | None = None
    trace: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self, *, include_challenge: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status.value,
            "task_id": self.task_id,
            "route": self.route.to_dict(),
            "result": self.result.to_dict() if self.result else None,
            "approval": self.approval.public_dict() if self.approval else None,
            "trace": list(self.trace),
        }
        if include_challenge and self.approval:
            payload["approval"]["challenge"] = self.approval.challenge
        return payload
