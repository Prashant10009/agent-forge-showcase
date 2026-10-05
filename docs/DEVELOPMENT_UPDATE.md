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

## Next seven days: October 6–12

This is a proposed seven-day sequence drawn from current engineering directions, not a previously committed release schedule. Each stage depends on the preceding evidence.

| Window | Focus | Reviewable outcome |
|---|---|---|
| Days 1–2 | Structural planning from current traces, handoffs, and known decision errors | Scoped plan, acceptance cases, dependencies, and a record of unresolved choices |
| Days 3–4 | Extend reviewed behavior evidence and replay sets | Source-linked examples, corrections, exclusion reasons, and a separately labelled evaluation set |
| Days 5–6 | Compare candidate decisions and watcher assessments with existing behavior | Error breakdowns, completion checks, resource measurements, and a recommendation on what is ready |
| Day 7 | Review the integrated workflow and publish the next evidence-backed update | Demonstrable changes, remaining limitations, and an updated implementation state |

The existing Python watcher provides observations for this work. A local-model watcher would require a suitable evaluation for signals the current typed triggers do not cover; its promotion is not presumed in this sequence.

Structural planning and build cycles can take one to two days of concentrated back-and-forth with models. The sequence remains plan → implement → replay and review → verify in the workflow. Completing a plan is not itself evidence that a feature is ready to release.

## What we are opening up

The public repository now explains the [evaluation framework](EVALUATION_FRAMEWORK.md), [historical leaderboard](LEADERBOARD.md), and [learning systems](LEARNING_SYSTEMS.md), and provides [recipes for your own components](BUILD_YOUR_OWN.md). The examples let readers inspect mechanisms without requiring a production account.

The next public updates should replace this dated snapshot with verified progress, keeping shipped capabilities, measured candidates, and plans distinguishable.

## What the deeper review changed

The latest merged implementation includes a logged-only Python watcher, richer timing attribution, and completion checks that account for observed file work. The separate local-model watcher remains planned. The [system guide](HOW_AGENT_FORGE_WORKS.md) now explains ordered council planning, capability-based assignment, proposal memory, and continuation context. The [behavior evaluation](BEHAVIOR_EVALUATION.md) publishes selected candidate measurements with their error tradeoffs.
