# Learning systems

Agent Forge keeps the models that execute work replaceable while retaining evidence about how the work went. Learning can change a route, improve retrieval, support a future classifier, or preserve a correction. Those are separate responsibilities.

## Concept map

| System | Evidence it uses | What it can influence | Current boundary |
|---|---|---|---|
| Karma | Eligible task outcomes, model capabilities, quality ratings, performance history | Candidate ranking and capability evidence | Guarded automatic learning is configured on; raw telemetry is broader than accepted learning |
| RTA / Niyati | Task and strategy outcomes plus runtime conditions | Strategy and runtime-management signals | Uses fallbacks when evidence is insufficient; outcome epochs separate incompatible history |
| Sampler learning | Call settings linked to later quality outcomes | Inference settings for a task/model/backend | Requires evidence before replacing presets |
| Task-pattern and council memory | Successful prior processes and recurring task shapes | Reuse of relevant routing or planning experience | Similarity, freshness, success, and vector-space checks constrain reuse |
| Feedback and learned rules | Explicit ratings, corrections, and confirmed classifications | Quality history, memory suitability, and future behavior | A saved conversation is not automatically an accepted training example |
| Retrieval encoder | Reviewed platform-specific training material | Finding relevant stored context | Fine-tuned GTE-ModernBERT is selected for several paths; migration remains per path |
| Learned decision heads | Curated decisions, outcomes, and reviewed behavior examples | Local answers to specific decision questions | Trained and measured, but disabled in the October 5 configuration |
| Structured decision service | Typed questions about a task and its state | Selected turn-start decisions; evidence for further evaluation | Jev is enabled on selected paths; most registered subsystem callers remain observational |
| Local watcher | Intended live workflow events and question catalogue | Notice issues and ask for a structured assessment | Planned, not enabled |

This is a committed-code and configuration snapshot reviewed October 5, 2026, not an assertion about the current health of a running instance.

## From observation to learning

Record what happened first. Then decide what the event is evidence of. A provider outage informs availability; an independently verified model error can inform task capability; an unsupported success claim remains unresolved. Keep the reason for including or excluding a record.

Where learned model-identity routing is being evaluated in shadow mode, the candidate signal is observed without deciding the route. Do not confuse a collected signal with an active policy change.

## How the training corpus grows

The platform's development creates plans, implementation history, build conversations, benchmark reviews, test results, and corrected failures. Selected runtime decisions and their outcomes add another source. Reviewed material supports training and evaluating the platform's own components.

A one-to-two-day planning and build cycle can be valuable because it preserves context and revision, not just an isolated answer. The system is the working environment; the corpus is a record of what was learned through building and using it.

Raw build conversations, operational records, and answer keys remain private. The [evaluation framework](EVALUATION_FRAMEWORK.md), [component recipes](BUILD_YOUR_OWN.md), public examples, and selected historical results are shared so others can inspect and adapt the ideas.

## What the public core demonstrates

The public `OutcomeLedger` and `EvidenceRouter` implement a small, deterministic example of outcome-informed selection. They are not a full reproduction of Karma, RTA, encoder training, or the Architect. The [evaluation-to-learning example](../examples/evaluation_learning_loop.py) adds a visible acceptance step; the [worker/runtime demo](../examples/worker_runtime_learning_demo.py) shows how accepted synthetic evidence can change the selected runtime without changing the worker's responsibility.

The external models' weights do not change when the public ledger changes. This distinction also matters in production: routing adaptation, memory, and training an in-house component are different mechanisms.
