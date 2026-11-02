# Learning systems

Architecture snapshot: 1 November 2026. This page describes how Agent Forge learns from its own work, at the
level its [public boundary](PUBLIC_BOUNDARY.md) allows. Weights, thresholds, prompts, training data and
learned parameters remain private.

Agent Forge learns in four separate ways. They are easy to blur, so this page keeps them apart:

| Mechanism | What changes | What it learns from | What it does not do |
|---|---|---|---|
| **Karma** (outcome scoring) | Per-model and per-category scores that routing reads | What each model actually did on a turn, judged after the turn | It does not change any model's weights |
| **Ṛta** (strategy advice) | Learned rewards per task type and strategy | Which execution strategy worked for which kind of task | It does not execute work itself |
| **Decision heads** (typed decisions) | Small in-house ModernBERT classifiers | Answers from a hosted typed-decision model, checked against turn outcomes | They do not answer a question they have not qualified for |
| **The retrieval encoder** | Agent Forge's fine-tuned GTE-ModernBERT encoder | Reviewed platform material, trained and evaluated offline | It does not train while the platform runs |

## Karma: credit goes to the model that did the work

After every turn, Karma records what each model did and decides afterwards whether the work was right. It
credits or debits the model that **actually executed** the work, not the one that was first assigned. A
plan step that fell over to another model is attributed to the model that finished it. Routing reads these
scores when it places the next call, so measured results, not habit, decide which model gets a role.

Karma is a measuring and scoring subsystem. It is not an agent and it does not answer users.

## Ṛta: which strategy, for which task

Ṛta advises on the shape of execution. It chooses among four named strategies: the chat owner working
alone, the planning council, the council followed by a decomposition into parallel subtasks (which falls
back to the chat owner alone when a gate declines it, and says so), and a wider council fan-out that is
considered only when enough backends are available. It keeps learned rewards per task type and strategy,
and its advice is one input the orchestrator weighs at the start of a turn.

## Typed decisions: one contract, a teacher and students

Many small questions recur on every turn: is this message trivial, which strategy fits, does this need
retrieval, should the council convene? Agent Forge asks all of them through **one decision service** with a
typed contract, so every caller asks the same way and every answer is recorded with its turn.

The answer comes from one of two places:
- a **hosted typed-decision model**, which acts as the teacher;
- Agent Forge's own **ModernBERT student heads**, which learn from the teacher's answers while the
  platform runs.

A head answers only a question it has qualified for, and falls back to the teacher when it is not
confident. A sample of the questions a head decides keeps going to the teacher, so the head is still
checked after it takes over.

**State on 1 November 2026:** five heads run (trivial, task type, strategy, needs-retrieval, council). Four
are in shadow: they answer in parallel and are measured, but do not decide. One, the trivial-message head,
decides at turn start.

## Retrieval: an encoder trained for this work

Memory is searched by meaning. Agent Forge's encoder is a GTE-ModernBERT model fine-tuned offline on
reviewed platform material and evaluated against the general-purpose encoder it replaced. It now serves
every memory store. Each store records which encoder version wrote each vector, so a query is only ever
compared with vectors from the same encoder.

If memory cannot be read, the platform says "memory unavailable". It never returns an empty result that
looks like "nothing relevant".

## What keeps learning honest

- **Outcome before credit.** A turn that claimed success is checked against what actually happened (files
  written, tests run, plan steps completed) before anyone is credited.
- **Shadow before authority.** A new decision head runs in shadow and is measured before it decides
  anything.
- **One vector space per read.** Two vectors from different encoders are never compared.
- **Review before training.** Examples are curated, checked for sensitive data, and held out from
  evaluation sets before they train anything.

Related: [how Agent Forge works](HOW_AGENT_FORGE_WORKS.md) · [behaviour evaluation](BEHAVIOR_EVALUATION.md) ·
[evaluation framework](EVALUATION_FRAMEWORK.md) · [build your own](BUILD_YOUR_OWN.md).
