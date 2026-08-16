"""End-to-end public control plane with routing, governance, execution, and state."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any

from .actions import PublicToolExecutor, default_tool_registry, plan_public_actions
from .adapters import AdapterRegistry, ScriptedAdapter
from .classification import classify
from .contracts import (
    LifecycleState,
    ManifestState,
    RiskLevel,
    RoutingPlan,
    RunIdentity,
    RunResult,
    RuntimeHealth,
    RuntimeProfile,
    WorkRequest,
)
from .control import (
    BudgetLedger,
    CancellationToken,
    CapacityRegistry,
    CircuitRegistry,
    DeadlineExceeded,
    OutcomeLedger,
    RunCancelled,
)
from .events import EventJournal
from .execution import ExecutionReport, ResilientExecutor
from .manifests import ActionManifest, ManifestRegistry
from .models import ActionKind, Capability
from .review import ReviewCouncil
from .selection import EvidenceRouter, NoEligibleRuntime
from .state import ArtifactStore, TenantStateStore


@dataclass(frozen=True, slots=True)
class ControlPlaneOutcome:
    state: LifecycleState
    request: WorkRequest
    plan: RoutingPlan | None
    manifest: ActionManifest | None
    result: RunResult | None
    events: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "run_id": self.request.identity.run_id,
            "plan": self.plan.to_dict() if self.plan else None,
            "manifest": self.manifest.public_dict() if self.manifest else None,
            "result": self.result.to_dict() if self.result else None,
            "events": list(self.events),
        }


@dataclass(slots=True)
class _PendingRun:
    request: WorkRequest
    plan: RoutingPlan
    manifest: ActionManifest
    journal: EventJournal
    token: CancellationToken


class PublicControlPlane:
    """A provider-neutral vertical slice of a governed orchestration platform."""

    def __init__(
        self,
        *,
        adapters: AdapterRegistry | None = None,
        state: TenantStateStore | None = None,
        artifacts: ArtifactStore | None = None,
        manifests: ManifestRegistry | None = None,
        circuits: CircuitRegistry | None = None,
        budgets: BudgetLedger | None = None,
        outcomes: OutcomeLedger | None = None,
        capacity: CapacityRegistry | None = None,
    ) -> None:
        self.state = state or TenantStateStore()
        self.artifacts = artifacts or ArtifactStore()
        self.manifests = manifests or ManifestRegistry()
        self.circuits = circuits or CircuitRegistry()
        self.budgets = budgets or BudgetLedger()
        self.outcomes = outcomes or OutcomeLedger()
        self.capacity = capacity or CapacityRegistry()
        self.adapters = adapters or default_adapter_registry()
        self.router = EvidenceRouter(self.circuits, self.outcomes)
        self.executor = ResilientExecutor(
            self.adapters,
            self.circuits,
            self.budgets,
            self.outcomes,
            self.capacity,
        )
        self.tools = PublicToolExecutor(
            default_tool_registry(self.artifacts),
            self.manifests,
        )
        self.review = ReviewCouncil()
        self._pending: dict[str, _PendingRun] = {}
        self._lock = RLock()

    def request(
        self,
        instruction: str,
        *,
        run_id: str = "run-1",
        tenant_id: str = "portfolio",
        session_id: str = "session-1",
        approval_scope: str = "turn-1",
        action: ActionKind = ActionKind.READ,
        risk: RiskLevel | None = None,
        expected_artifacts: tuple[str, ...] = (),
        deadline_ms: int = 5_000,
        max_attempts: int = 3,
        budget_limit: float = 1.0,
    ) -> WorkRequest:
        classification = classify(instruction)
        resolved_risk = risk or (
            RiskLevel.HIGH
            if action in {ActionKind.WRITE, ActionKind.EXECUTE}
            else RiskLevel.MEDIUM
            if action is ActionKind.NETWORK
            else RiskLevel.LOW
        )
        return WorkRequest(
            identity=RunIdentity(run_id, tenant_id, session_id, approval_scope),
            instruction=instruction,
            required=classification.required,
            preferred=classification.preferred,
            action=action,
            risk=resolved_risk,
            deadline_ms=deadline_ms,
            max_attempts=max_attempts,
            budget_limit=budget_limit,
            expected_artifacts=expected_artifacts,
            metadata={
                "classification": classification.kind,
                "classification_evidence": classification.evidence,
            },
        )

    def start(self, request: WorkRequest) -> ControlPlaneOutcome:
        journal = EventJournal(request.identity)
        token = CancellationToken(request.deadline_ms)
        self.state.transition(request.identity.run_id, request.identity.tenant_id, LifecycleState.ACCEPTED)
        journal.emit("intake", LifecycleState.ACCEPTED, {"action": request.action.value})
        journal.emit(
            "classification",
            LifecycleState.CLASSIFIED,
            {
                "kind": request.metadata.get("classification", "explicit"),
                "evidence": list(request.metadata.get("classification_evidence", ())),
                "required": [item.value for item in request.required],
            },
        )

        memories = self.state.recent(
            request.identity.tenant_id,
            session_id=request.identity.session_id,
            query=request.instruction,
        )
        journal.emit(
            "context",
            LifecycleState.CONTEXT_READY,
            {"memory_records": len(memories), "tenant_scoped": True},
        )

        review = self.review.evaluate(request)
        journal.emit(
            "review",
            LifecycleState.REVIEWED,
            {
                "required": review.required,
                "approved_to_route": review.approved_to_route,
                "findings": [finding.perspective for finding in review.findings],
            },
        )
        if not review.approved_to_route:
            return self._terminal_failure(request, None, journal, "review denied request")

        try:
            plan = self.router.plan(request, self.adapters.profiles())
        except NoEligibleRuntime as error:
            return self._terminal_failure(request, None, journal, str(error))
        journal.emit(
            "routing",
            LifecycleState.ROUTED,
            {"selected": plan.selected, "fallbacks": list(plan.fallbacks)},
        )

        actions = plan_public_actions(request.instruction, request.expected_artifacts)
        manifest, disposition = self.manifests.create_or_reuse(request.identity, actions)
        approval_required = any(
            action.risk in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL}
            for action in actions
        )
        if approval_required:
            journal.emit(
                "governance",
                LifecycleState.APPROVAL_REQUIRED,
                {
                    "manifest_id": manifest.manifest_id,
                    "fingerprint": manifest.fingerprint,
                    "disposition": disposition,
                    "action_count": len(manifest.actions),
                },
            )
            pending = _PendingRun(request, plan, manifest, journal, token)
            with self._lock:
                self._pending[manifest.manifest_id] = pending
            self.state.save_checkpoint(
                request.identity.run_id,
                request.identity.tenant_id,
                request.identity.session_id,
                {
                    "state": LifecycleState.APPROVAL_REQUIRED.value,
                    "manifest_id": manifest.manifest_id,
                    "fingerprint": manifest.fingerprint,
                },
            )
            return ControlPlaneOutcome(
                LifecycleState.APPROVAL_REQUIRED,
                request,
                plan,
                manifest,
                None,
                journal.public_snapshot(),
            )

        self.manifests.approve(manifest.manifest_id, request.identity)
        pending = _PendingRun(request, plan, manifest, journal, token)
        return self._execute(pending)

    def approve(self, manifest_id: str, identity: RunIdentity) -> ControlPlaneOutcome:
        with self._lock:
            pending = self._pending.get(manifest_id)
        if pending is None:
            raise KeyError("unknown pending run")
        self.manifests.approve(manifest_id, identity)
        pending.journal.emit(
            "governance",
            LifecycleState.RUNNING,
            {"manifest_id": manifest_id, "approved": True},
        )
        with self._lock:
            self._pending.pop(manifest_id, None)
        return self._execute(pending)

    def reject(
        self,
        manifest_id: str,
        identity: RunIdentity,
        reason: str = "rejected by operator",
    ) -> ControlPlaneOutcome:
        with self._lock:
            pending = self._pending.pop(manifest_id, None)
        if pending is None:
            raise KeyError("unknown pending run")
        manifest = self.manifests.reject(manifest_id, identity, reason)
        pending.token.cancel(reason)
        result = RunResult(
            pending.request.identity.run_id,
            LifecycleState.CANCELLED,
            error=reason,
        )
        pending.journal.emit(
            "governance",
            LifecycleState.CANCELLED,
            {"manifest_id": manifest_id, "reason": reason},
        )
        self.state.transition(
            pending.request.identity.run_id,
            pending.request.identity.tenant_id,
            LifecycleState.CANCELLED,
        )
        return ControlPlaneOutcome(
            LifecycleState.CANCELLED,
            pending.request,
            pending.plan,
            manifest,
            result,
            pending.journal.public_snapshot(),
        )

    def cancel(self, manifest_id: str, reason: str = "cancelled by operator") -> None:
        with self._lock:
            pending = self._pending.get(manifest_id)
        if pending is None:
            raise KeyError("unknown pending run")
        pending.token.cancel(reason)

    def _execute(self, pending: _PendingRun) -> ControlPlaneOutcome:
        request, plan, manifest, journal, token = (
            pending.request,
            pending.plan,
            pending.manifest,
            pending.journal,
            pending.token,
        )
        if journal.snapshot()[-1].state is not LifecycleState.RUNNING:
            journal.emit("execution", LifecycleState.RUNNING, {"runtime": plan.selected})
        self.state.transition(request.identity.run_id, request.identity.tenant_id, LifecycleState.RUNNING)
        try:
            execution = self.executor.execute(request, plan, token)
            if not execution.success:
                self._terminalize_manifest(
                    manifest,
                    request.identity,
                    "runtime execution failed before action claim",
                )
                return self._terminal_failure(
                    request,
                    plan,
                    journal,
                    execution.error,
                    execution,
                    manifest,
                )
            action_results = self.tools.execute_manifest(manifest, request.identity, token)
            artifact_ids = tuple(
                artifact_id
                for action_result in action_results
                for artifact_id in action_result.artifact_ids
            )
            journal.emit(
                "verification",
                LifecycleState.VERIFYING,
                {
                    "non_empty_output": bool(execution.output.strip()),
                    "actions_succeeded": all(result.success for result in action_results),
                    "artifact_count": len(artifact_ids),
                },
            )
            verification = {
                "non_empty_output": bool(execution.output.strip()),
                "actions_succeeded": all(result.success for result in action_results),
                "expected_artifacts_present": len(artifact_ids) >= len(request.expected_artifacts),
            }
            if not all(verification.values()):
                return self._terminal_failure(
                    request,
                    plan,
                    journal,
                    "verification contract failed",
                    execution,
                    manifest,
                )
            self.state.append_memory(
                request.identity.tenant_id,
                request.identity.session_id,
                "user",
                request.instruction,
            )
            self.state.append_memory(
                request.identity.tenant_id,
                request.identity.session_id,
                "assistant",
                execution.output,
            )
            result = RunResult(
                request.identity.run_id,
                LifecycleState.COMPLETED,
                output=execution.output,
                runtime_name=execution.runtime_name,
                attempts=execution.attempts,
                actions=action_results,
                artifact_ids=artifact_ids,
                verification=verification,
                spent=execution.spent,
            )
            journal.emit(
                "completion",
                LifecycleState.COMPLETED,
                {"runtime": execution.runtime_name, "spent": execution.spent},
            )
            self.state.transition(
                request.identity.run_id,
                request.identity.tenant_id,
                LifecycleState.COMPLETED,
            )
            self.state.save_checkpoint(
                request.identity.run_id,
                request.identity.tenant_id,
                request.identity.session_id,
                result.to_dict(),
            )
            return ControlPlaneOutcome(
                LifecycleState.COMPLETED,
                request,
                plan,
                manifest,
                result,
                journal.public_snapshot(),
            )
        except (RunCancelled, DeadlineExceeded) as error:
            self._terminalize_manifest(manifest, request.identity, str(error))
            result = RunResult(
                request.identity.run_id,
                LifecycleState.CANCELLED,
                error=str(error),
            )
            journal.emit("execution", LifecycleState.CANCELLED, {"reason": str(error)})
            self.state.transition(
                request.identity.run_id,
                request.identity.tenant_id,
                LifecycleState.CANCELLED,
            )
            return ControlPlaneOutcome(
                LifecycleState.CANCELLED,
                request,
                plan,
                manifest,
                result,
                journal.public_snapshot(),
            )
        except Exception as error:
            self._terminalize_manifest(
                manifest,
                request.identity,
                f"execution error: {type(error).__name__}",
            )
            return self._terminal_failure(
                request,
                plan,
                journal,
                f"{type(error).__name__}: {error}",
                manifest=manifest,
            )

    def _terminal_failure(
        self,
        request: WorkRequest,
        plan: RoutingPlan | None,
        journal: EventJournal,
        error: str,
        execution: ExecutionReport | None = None,
        manifest: ActionManifest | None = None,
    ) -> ControlPlaneOutcome:
        result = RunResult(
            request.identity.run_id,
            LifecycleState.FAILED,
            attempts=execution.attempts if execution else (),
            error=error,
            spent=execution.spent if execution else 0.0,
        )
        journal.emit("completion", LifecycleState.FAILED, {"error": error})
        self.state.transition(
            request.identity.run_id,
            request.identity.tenant_id,
            LifecycleState.FAILED,
        )
        return ControlPlaneOutcome(
            LifecycleState.FAILED,
            request,
            plan,
            manifest,
            result,
            journal.public_snapshot(),
        )

    def _terminalize_manifest(
        self,
        manifest: ActionManifest,
        identity: RunIdentity,
        reason: str,
    ) -> None:
        """Best-effort terminalization prevents orphaned approval capabilities."""

        if manifest.state in {ManifestState.PENDING, ManifestState.APPROVED}:
            self.manifests.reject(manifest.manifest_id, identity, reason)
        elif manifest.state is ManifestState.EXECUTING:
            self.manifests.complete(manifest.manifest_id, success=False)


def default_adapter_registry() -> AdapterRegistry:
    return AdapterRegistry(
        (
            ScriptedAdapter(
                RuntimeProfile(
                    "reasoning-core",
                    frozenset({Capability.TEXT, Capability.REASONING}),
                    RuntimeHealth.HEALTHY,
                    reliability=0.94,
                    latency_ms=90,
                    unit_cost=0.08,
                )
            ),
            ScriptedAdapter(
                RuntimeProfile(
                    "tool-worker",
                    frozenset(
                        {Capability.TEXT, Capability.CODE, Capability.DATA, Capability.TOOLS}
                    ),
                    RuntimeHealth.HEALTHY,
                    reliability=0.91,
                    latency_ms=120,
                    unit_cost=0.06,
                    supports_tools=True,
                )
            ),
            ScriptedAdapter(
                RuntimeProfile(
                    "resilient-worker",
                    frozenset(
                        {
                            Capability.TEXT,
                            Capability.CODE,
                            Capability.DATA,
                            Capability.TOOLS,
                            Capability.REASONING,
                        }
                    ),
                    RuntimeHealth.DEGRADED,
                    reliability=0.86,
                    latency_ms=180,
                    unit_cost=0.04,
                    supports_tools=True,
                )
            ),
            ScriptedAdapter(
                RuntimeProfile(
                    "vision-worker",
                    frozenset({Capability.TEXT, Capability.VISION, Capability.REASONING}),
                    RuntimeHealth.HEALTHY,
                    reliability=0.89,
                    latency_ms=150,
                    unit_cost=0.07,
                )
            ),
        )
    )
