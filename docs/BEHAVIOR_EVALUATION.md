# Evaluating how the system manages work

Agent Forge evaluates the decisions surrounding a model call as well as the answer itself. A capable model can still be sent the wrong task, given an incomplete plan, interrupted at the wrong time, or credited for work that never happened.

The behavior dataset builder and review process target eight practical questions. These are public concept descriptions, not production prompts or a release of training examples.

| Behavior | What the evaluation asks | A useful hard case |
|---|---|---|
| Council selection | Does this task need deeper coordinated planning? | A long request that only needs one answer |
| Work splitting | How much independent work can run at once? | Several deliverables with dependencies between them |
| Step capability | What strength does this step require? | A coding project whose next step is research or verification |
| Completion | Was the requested work actually delivered? | A confident description of a file that was never created |
| Scope | Does this action belong to the request? | A necessary supporting edit versus an unrelated configuration change |
| Escalation | Which level should handle the next decision? | A repairable local problem versus a choice requiring the owner |
| Task identity | Is this the same task, a related task, or different work? | Similar words describing different projects |
| Continuation | Is this message trivial or does it advance existing work? | “And the tests?” after an implementation request |

These are targets for dataset construction and evaluation. They are not eight fully deployed learned policies.

## What a reviewed example carries

An example needs the situation the decision saw, its source, the proposed answer, available outcome evidence, and any review or correction. Different decisions need different inputs: previous conversation for continuation, plan context for step capability, observed work for completion.

The implementation mines real requests, turns, plan steps, and task pairs. It queues low-confidence or contradictory labels for review. Completion examples cannot silently substitute a short answer preview for the actual recorded reply. Inferred request context is kept distinct from verified context.

Related conversations are grouped for splitting where available; task-pair evaluation also needs explicit overlap checks. Counterfactual edits inherit source provenance and are excluded from test. Checks cover duplication, test traffic, sensitive material, customer-data clearance, and held-out content appearing either as the main input or inside context. A dataset build and a successful review are separate milestones.

## A measured lesson: review changes what the model learns

The October 3, 2026 first measurement compared learned candidates with the then-current rules on private, hand-labelled replay turns. Candidate selection used training-side validation. The headline replay examples and their source chats were excluded from training.

| Decision | Reviewed-label candidate | Rule baseline | What the count leaves out |
|---|---:|---:|---|
| Trivial versus substantive message | 83 / 85 correct | 78 / 85 correct | Only 12 trivial examples; a small first measurement |
| Council needed versus not needed | 70 / 75 correct | 67 / 75 correct | Only 6 examples needed a council; class-specific errors matter |

For council selection, false council calls fell from **6 to 2** among 69 cases that did not need one. But the candidate found **3 of the 6** cases that did need one, compared with **4 of 6** for the rule. A policy decision must weigh both kinds of error. “Never use a council” would score 69/75 accuracy on this imbalanced set while missing every positive.

The selected trivial-message candidate made no false “trivial” calls on the replay set. However, the small sample does not establish a general performance win. The fan-out candidate did not beat the baseline on its headline proxy, and that proxy was itself weak.

Review was material: raw teacher labels included continuation and council-selection mistakes. Training on reviewed labels changed the behavior. This is why the system treats teacher answers as proposed labels and keeps the review history.

Both measured decision candidates remain disabled in the October 5 configuration. These are maintainer-reported historical measurements, not independently reproducible public benchmark results. They came from one founder's data, one reviewer, one training seed, and a small replay set; negative labels in the broader behavior set were sampled rather than exhaustively reviewed.

## Evaluate retrieval for its own job

Retrieval asks whether the right prior context is found. It does not measure council judgment or overall assistant quality. The corrected October 3 round-three encoder evaluation compared several stores, a second training seed, and the production encoding path. Results were approximately tied on builder logs and task states, better on Architect memory, and better on a first-sentence insurance retrieval proxy while tied on its harder set.

The report revised earlier conclusions after correcting evaluation text and ranking issues. The generalizable lesson is to match training and serving inputs, retain superseded results, and report uncertainty by task. A favourable retrieval result does not establish domain decision quality.

## Evaluate whether a model is needed

An October 4 local watcher experiment tested choosing a question and selecting its context from typed event windows. None of the small-model candidates met the experiment's bar; deterministic Python rules handled those constructed triggers more reliably. That supports the implemented Python event watcher for this bounded job. It does not establish that rules solve open-ended supervision, which the experiment did not test.

The public [leaderboard](LEADERBOARD.md) covers model task performance. This guide covers control decisions and component evidence. Keep those comparisons separate when building your own [evaluation framework](EVALUATION_FRAMEWORK.md).
