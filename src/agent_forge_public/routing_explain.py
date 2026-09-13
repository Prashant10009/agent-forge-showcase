"""Human-readable routing explanations for the public reference core.

The explanation is derived only from the already-public RoutingPlan contract. It does
not expose or infer any production policy.
"""

from __future__ import annotations

from typing import Any

from .contracts import CandidateScore, RoutingPlan
from .worker_templates import WorkerKind


def _candidate_view(candidate: CandidateScore) -> dict[str, Any]:
    return {
        "runtime": candidate.runtime_name,
        "eligible": candidate.eligible,
        "score": candidate.total if candidate.eligible else None,
        "components": dict(candidate.components),
        "reasons": list(candidate.reasons),
    }


def explain_plan(
    plan: RoutingPlan,
    *,
    worker: WorkerKind | str | None = None,
) -> dict[str, Any]:
    """Return an audit-friendly explanation of a public routing plan."""

    resolved_worker = WorkerKind(worker).value if worker is not None else None
    selected = next(
        candidate
        for candidate in plan.candidates
        if candidate.runtime_name == plan.selected
    )
    exclusions = [
        _candidate_view(candidate)
        for candidate in plan.candidates
        if not candidate.eligible
    ]
    eligible = sorted(
        (candidate for candidate in plan.candidates if candidate.eligible),
        key=lambda candidate: (-candidate.total, candidate.runtime_name),
    )
    return {
        "run_id": plan.run_id,
        "specialist_worker": resolved_worker,
        "selected_runtime": plan.selected,
        "selected_score": selected.total,
        "fallbacks": list(plan.fallbacks),
        "eligible_ranked": [_candidate_view(candidate) for candidate in eligible],
        "excluded": exclusions,
        "policy_label": plan.policy_label,
        "production_policy": False,
    }
