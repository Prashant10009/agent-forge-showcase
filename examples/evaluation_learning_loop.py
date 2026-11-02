"""Synthetic, offline evaluation-to-learning example; not production policy.

Run after installing the public package: python examples/evaluation_learning_loop.py
The checks here are fixture observations, not real provider or artifact executions.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite

from agent_forge_public.control import OutcomeLedger


@dataclass(frozen=True)
class Episode:
    episode_id: str
    tenant: str
    task_family: str
    runtime: str
    verified: bool
    success: bool
    cause: str  # completed | model | platform | unknown
    assisted: bool = False
    latency_ms: float = 0.0
    cost: float = 0.0


def assess(episode: Episode) -> tuple[bool, str]:
    """An illustrative acceptance policy chosen for this example only."""
    if not all((episode.episode_id, episode.tenant, episode.task_family, episode.runtime)):
        return False, "missing_identity"
    if not all(isfinite(v) and v >= 0 for v in (episode.latency_ms, episode.cost)):
        return False, "invalid_measurement"
    if episode.assisted:
        return False, "keep_assisted_separate"
    if episode.cause == "platform":
        return False, "availability_evidence_only"
    if not episode.verified:
        return False, "outcome_unverified"
    if episode.success and episode.cause == "completed":
        return True, "verified_completion"
    if not episode.success and episode.cause == "model":
        return True, "verified_model_error"
    return False, "attribution_unresolved"


def collect(episodes: tuple[Episode, ...]) -> dict:
    """Audit everything; keep task families and tenants in separate ledgers."""
    ledgers: dict[str, OutcomeLedger] = {}
    identities: set[tuple[str, str, str]] = set()
    seen: set[tuple[str, str]] = set()
    audit = []
    for episode in episodes:
        identity = (episode.tenant, episode.episode_id)
        accepted, reason = assess(episode)
        if identity in seen:
            accepted, reason = False, "duplicate_episode"
        seen.add(identity)
        audit.append({"episode": episode.episode_id, "accepted": accepted, "reason": reason})
        if not accepted:
            continue
        ledger = ledgers.setdefault(episode.task_family, OutcomeLedger())
        ledger.record(episode.tenant, episode.runtime, success=episode.success,
                      latency_ms=episode.latency_ms, cost=episode.cost)
        identities.add((episode.task_family, episode.tenant, episode.runtime))
    summaries = []
    for family, tenant, runtime in sorted(identities):
        stats = ledgers[family].get(tenant, runtime)
        summaries.append({"task_family": family, "tenant": tenant, "runtime": runtime,
                          "successes": stats.successes, "failures": stats.failures})
    return {"synthetic": True, "production_policy": False,
            "audit": audit, "accepted_outcomes": summaries}


def sample_episodes() -> tuple[Episode, ...]:
    return (
        Episode("checked-parser", "sample", "code", "runtime-a", True, True,
                "completed", latency_ms=120, cost=0.1),
        Episode("wrong-parser", "sample", "code", "runtime-b", True, False,
                "model", latency_ms=140, cost=0.1),
        Episode("provider-unavailable", "sample", "code", "runtime-a", True, False,
                "platform", latency_ms=20),
        Episode("claims-file-exists", "sample", "code", "runtime-b", False, True,
                "completed", latency_ms=100, cost=0.1),
        Episode("corrected-by-reviewer", "sample", "code", "runtime-b", True, True,
                "completed", assisted=True, latency_ms=180, cost=0.2),
        Episode("unclear-cause", "sample", "code", "runtime-a", True, False,
                "unknown", latency_ms=160, cost=0.1),
    )


if __name__ == "__main__":
    print(json.dumps(collect(sample_episodes()), indent=2))
