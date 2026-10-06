# Learning systems

Agent Forge keeps the models that execute work replaceable while retaining evidence about how the work went. Learning can change a route, improve retrieval, improve a classifier, or preserve a correction. Those are separate responsibilities.

## Concept map

| System | Evidence it uses | What it can influence | Evidence discipline |
|---|---|---|---|
| Karma | Eligible task outcomes, model capabilities, quality ratings, performance history | Candidate ranking and capability evidence | Raw telemetry is broader than accepted learning evidence |
| RTA / Niyati | Task and strategy outcomes plus runtime conditions | Strategy and runtime-management signals | Uses fallbacks when evidence is insufficient; outcome epochs separate incompatible history |
| Sampler learning | Call settings linked to later quality outcomes | Inference settings for a task/model/backend | Requires evidence before replacing presets |
| Task-pattern and council memory | Successful prior processes and recurring task shapes | Reuse of relevant routing or planning experience | Similarity, freshness, success, and vector-space checks constrain reuse |
| Feedback and learned rules | Explicit ratings, corrections, and confirmed classifications | Quality history, memory suitability, and future behavior | A saved conversation is not automatically an accepted training example |
| Retrieval encoder | Reviewed platform-specific training material | Finding relevant stored context | GTE-ModernBERT retrieval and ModernColBERT reranking are evaluated for relevance and serving cost |
| Learned decision heads | Curated decisions, outcomes, and reviewed behavior examples | Local answers to specific decision questions | Each head qualifies against the decision it replaces |
| Structured decision service | Typed questions about a task and its state | Workflow assessments and evidence for further evaluation | Typed answers are validated; each caller retains its authority and fallback behavior |
| Workflow observation | Typed workflow events and bounded task context | Ask structured questions and collect assessments | Observation, assessment, and action are separate responsibilities |

These mechanisms connect the task lifecycle to learning at the model, strategy, memory, and component levels.

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

## Learning to manage work

The behavior pipeline targets council selection, work splitting, step capability, completion, scope, escalation, task identity, and continuation. It mines different source shapes for different questions rather than treating every conversation as one generic training pair. See the [behavior evaluation](BEHAVIOR_EVALUATION.md) for concrete measurements and the [system guide](HOW_AGENT_FORGE_WORKS.md) for how those decisions connect.

The Architect also retains decided proposals and rejection reasons. That memory can improve a later proposal without updating a model’s weights. The Python watcher supplies another observation path: workflow event → typed question → logged assessment → review against outcomes. Neither a stored assessment nor an approved proposal is automatically a successful training label.

## Decision and retrieval architecture

The [stack guide](DECISION_AND_RETRIEVAL_STACK.md) explains how Jev, GTE-ModernBERT retrieval, learned decision heads, ModernColBERT reranking, and ONNX work together. The platform retains operational knowledge while the models executing specialist work remain replaceable.
