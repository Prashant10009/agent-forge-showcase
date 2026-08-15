"""Composable public orchestration lifecycle: classify, route, govern, execute, trace."""

from __future__ import annotations

from threading import RLock

from .classification import classify
from .governance import ApprovalGate
from .models import ActionKind, RouteDecision, RunOutcome, RunStatus, TaskSpec
from .routing import CapabilityRouter
from .runtime import RuntimeRegistry, default_registry
from .tracing import TraceRecorder


class AgentForge:
    """Provider-neutral public reference implementation of the Agent Forge lifecycle."""

    def __init__(
        self,
        registry: RuntimeRegistry | None = None,
        router: CapabilityRouter | None = None,
        approvals: ApprovalGate | None = None,
        trace: TraceRecorder | None = None,
    ) -> None:
        self.registry = registry or default_registry()
        self.router = router or CapabilityRouter()
        self.approvals = approvals or ApprovalGate()
        self.trace = trace or TraceRecorder()
        self._pending: dict[str, tuple[TaskSpec, RouteDecision]] = {}
        self._lock = RLock()

    def make_task(
        self,
        instruction: str,
        *,
        task_id: str = "task-1",
        action: ActionKind = ActionKind.READ,
    ) -> TaskSpec:
        classification = classify(instruction)
        return TaskSpec(
            task_id=task_id,
            instruction=instruction,
            required=classification.required,
            preferred=classification.preferred,
            action=action,
            metadata={
                "classification": classification.kind,
                "classification_evidence": classification.evidence,
            },
        )

    def submit(self, task: TaskSpec) -> RunOutcome:
        self.trace.clear()
        self.trace.emit("intake", "accepted", {"task_id": task.task_id, "action": task.action.value})
        self.trace.emit(
            "classification",
            "completed",
            {
                "kind": task.metadata.get("classification", "explicit"),
                "evidence": list(task.metadata.get("classification_evidence", ())),
            },
        )
        route = self.router.choose(task, self.registry.descriptors())
        self.trace.emit(
            "routing",
            "selected",
            {"runtime": route.runtime_name, "score": route.score, "considered": dict(route.considered)},
        )

        if self.approvals.policy.requires_approval(task):
            request = self.approvals.request(task)
            with self._lock:
                self._pending[request.approval_id] = (task, route)
            self.trace.emit(
                "governance",
                "approval_required",
                {"approval_id": request.approval_id, "action": task.action.value},
            )
            return RunOutcome(
                RunStatus.APPROVAL_REQUIRED,
                task.task_id,
                route,
                approval=request,
                trace=self.trace.snapshot(),
            )

        return self._execute(task, route)

    def resume(self, approval_id: str, challenge: str) -> RunOutcome:
        with self._lock:
            pending = self._pending.get(approval_id)
        if pending is None:
            raise KeyError("unknown pending run")
        task, route = pending
        self.approvals.consume(approval_id, challenge, task_id=task.task_id)
        with self._lock:
            self._pending.pop(approval_id, None)
        self.trace.emit("governance", "approved", {"approval_id": approval_id})
        return self._execute(task, route)

    def _execute(self, task: TaskSpec, route: RouteDecision) -> RunOutcome:
        self.trace.emit("execution", "started", {"runtime": route.runtime_name})
        result = self.registry.execute(route.runtime_name, task)
        self.trace.emit(
            "execution",
            "completed",
            {"runtime": result.runtime_name, "duration_ms": round(result.duration_ms, 4)},
        )
        self.trace.emit("verification", "completed", {"non_empty_output": bool(result.output.strip())})
        return RunOutcome(
            RunStatus.COMPLETED,
            task.task_id,
            route,
            result=result,
            trace=self.trace.snapshot(),
        )
