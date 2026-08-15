"""One-time approval boundaries for side-effecting public-core tasks."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock

from .models import ActionKind, ApprovalRequest, TaskSpec


class ApprovalError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PublicGovernancePolicy:
    approval_actions: frozenset[ActionKind] = frozenset(
        {ActionKind.WRITE, ActionKind.EXECUTE, ActionKind.NETWORK}
    )

    def requires_approval(self, task: TaskSpec) -> bool:
        return task.action in self.approval_actions


@dataclass(slots=True)
class _PendingApproval:
    request: ApprovalRequest
    challenge_digest: str
    consumed: bool = False


class ApprovalGate:
    """Issues single-use challenges and rejects replayed approvals."""

    def __init__(
        self,
        policy: PublicGovernancePolicy | None = None,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        self.policy = policy or PublicGovernancePolicy()
        self._token_factory = token_factory or (lambda: secrets.token_urlsafe(24))
        self._pending: dict[str, _PendingApproval] = {}
        self._lock = RLock()

    def request(self, task: TaskSpec) -> ApprovalRequest:
        challenge = self._token_factory()
        approval_id = hashlib.sha256(f"{task.task_id}:{challenge}".encode()).hexdigest()[:16]
        request = ApprovalRequest(
            approval_id=approval_id,
            task_id=task.task_id,
            action=task.action,
            summary=f"Authorize {task.action.value}: {task.instruction}",
            challenge=challenge,
        )
        with self._lock:
            self._pending[approval_id] = _PendingApproval(request, self._digest(challenge))
        return request

    def consume(self, approval_id: str, challenge: str, *, task_id: str) -> None:
        with self._lock:
            pending = self._pending.get(approval_id)
            if pending is None:
                raise ApprovalError("unknown approval request")
            if pending.consumed:
                raise ApprovalError("approval has already been consumed")
            if pending.request.task_id != task_id:
                raise ApprovalError("approval does not belong to this task")
            if not hmac.compare_digest(pending.challenge_digest, self._digest(challenge)):
                raise ApprovalError("invalid approval challenge")
            pending.consumed = True

    @staticmethod
    def _digest(challenge: str) -> str:
        return hashlib.sha256(challenge.encode()).hexdigest()
