"""Bounded multi-perspective review for consequential public-core requests."""

from __future__ import annotations

from .contracts import ReviewFinding, ReviewReport, RiskLevel, WorkRequest


class ReviewCouncil:
    """Rule-based perspectives that expose review structure without private prompts."""

    def evaluate(self, request: WorkRequest) -> ReviewReport:
        required = request.risk in {RiskLevel.HIGH, RiskLevel.CRITICAL} or bool(
            request.expected_artifacts
        )
        if not required:
            return ReviewReport(False, (), True, "bounded read-only work")

        findings: list[ReviewFinding] = []
        if request.expected_artifacts:
            findings.append(
                ReviewFinding(
                    "creation",
                    RiskLevel.LOW,
                    f"deliverables are explicit: {', '.join(request.expected_artifacts)}",
                    "verify every declared artifact before completion",
                )
            )
        if request.action.value in {"write", "execute", "network"}:
            findings.append(
                ReviewFinding(
                    "preservation",
                    RiskLevel.HIGH,
                    f"{request.action.value} authority can create side effects",
                    "capture exact actions in a tenant-scoped manifest",
                )
            )
        lowered = request.instruction.casefold()
        deny = "bypass approval" in lowered or "ignore governance" in lowered
        if deny:
            findings.append(
                ReviewFinding(
                    "risk",
                    RiskLevel.CRITICAL,
                    "request attempts to bypass the control boundary",
                    "deny before routing",
                )
            )
        else:
            findings.append(
                ReviewFinding(
                    "verification",
                    RiskLevel.MEDIUM,
                    "completion must be supported by output and artifact checks",
                    "emit one terminal event only after verification",
                )
            )
        return ReviewReport(
            True,
            tuple(findings),
            not deny,
            "consequential work received bounded multi-perspective review",
        )
