# Development update — October 5, 2026

Agent Forge is a working orchestration system and an ongoing body of evaluated engineering work. The planning, model collaboration, implementation, and correction used to build it also produce material for training its own components.

## Current implementation

| Area | State | What it means |
|---|---|---|
| Orchestrated execution | Implemented | Primary chat ownership, specialist workers, ordered council planning, tools, and persistent context |
| Outcome evidence | Implemented | Records connect the actual executor and performed work to completion and failure information |
| Evaluation and guarded learning | Implemented | Benchmark reviews, output evaluation, workflow evidence, ratings, and eligibility checks serve different purposes |
| Structured decision service | Selected paths enabled | Jev supplies selected turn-start decisions; the shared interface supports wider use with most subsystem callers primarily observational |
| Fine-tuned retrieval encoder | Selected paths enabled | Current configuration selects GTE-ModernBERT for builder logs, architect memory, task-state retrieval, and insurance knowledge with guarded fallbacks |
| Learned decision heads | Trained and evaluated; disabled | Candidates must qualify before replacing a decision |
| Python event watcher | Implemented; logged-only | Observes workflow events, asks typed questions, and records assessments without acting on them |
| Local-model watcher | Planned; candidates evaluated | Proposed model-based observation remains separate from the shipped Python watcher |

This describes committed implementation and configuration reviewed on October 5. It is not a live service-status assertion. The runnable public core is a smaller reference implementation; see the [learning map](LEARNING_SYSTEMS.md) for those boundaries.

## Immediate production target: October 6

The founder has set October 6 as the production-completion target for the connected Jev / ModernBERT / ModernColBERT transition and BGE-M3 retirement. The [stack guide](DECISION_AND_RETRIEVAL_STACK.md) explains both the intended architecture and the verified October 5 starting point.

| Workstream | Target behavior |
|---|---|
| Jev across automations | Python subsystems use typed assessments to resolve ambiguity while retaining their responsibilities and action controls |
| In-house ModernBERT | Reviewed platform experience supports retrieval and qualified local decision heads |
| ModernColBERT | Rerank the dense retrieval shortlist before passing selected context onward |
| BGE-M3 retirement | Complete the remaining dependent reads, writes, classifiers, and cache transitions before removing the old runtime |

This target was confirmed by the founder on October 5. The dated implementation table above remains the last verified starting state, rather than a claim that tomorrow's rollout has already completed.

## Following the rollout: October 7–12

Review actual workflow outcomes, replay decision errors, examine retrieval and context handoffs, and publish the resulting production state. These are follow-through priorities, not a newly imposed seven-day implementation schedule.

Structural planning and build cycles can take one to two days of concentrated back-and-forth with models. Plans, disagreements, corrections, and verified outcomes from that process continue to supply material for the learning pipeline.

## What we are opening up

The public repository now explains the [evaluation framework](EVALUATION_FRAMEWORK.md), [historical leaderboard](LEADERBOARD.md), and [learning systems](LEARNING_SYSTEMS.md), and provides [recipes for your own components](BUILD_YOUR_OWN.md). The examples let readers inspect mechanisms without requiring a production account.

The next public updates should replace this dated snapshot with verified progress, keeping shipped capabilities, measured candidates, and plans distinguishable.

## What the deeper review changed

The latest merged implementation includes a logged-only Python watcher, richer timing attribution, and completion checks that account for observed file work. The separate local-model watcher remains planned. The [system guide](HOW_AGENT_FORGE_WORKS.md) now explains ordered council planning, capability-based assignment, proposal memory, and continuation context. The [behavior evaluation](BEHAVIOR_EVALUATION.md) publishes selected candidate measurements with their error tradeoffs.

## Decision and retrieval migration

The [decision and retrieval stack](DECISION_AND_RETRIEVAL_STACK.md) explains Jev’s current role, the distinction between active GTE-ModernBERT retrieval and inactive learned decision heads, the planned ModernColBERT reranker, and the BGE-M3 dependencies still being migrated. The target is evaluated in-house decisions and context selection, with hosted decision support where appropriate. BGE retirement is in progress, not complete.
