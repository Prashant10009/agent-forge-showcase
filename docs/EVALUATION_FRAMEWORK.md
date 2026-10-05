# Evaluation framework

Agent Forge is evaluated as a system that plans, calls models and tools, receives feedback, and delivers work. Its evaluation record also includes the sustained planning and implementation work used to build the platform itself.

The reusable idea is to preserve the relationship between **situation → decision → action → evidence → correction → outcome**. A final answer alone cannot explain which part of a workflow succeeded or failed.

## Six complementary views

| Evaluation | Question | Evidence |
|---|---|---|
| Ground-truth tasks / Forge-Bench | Can a model make accurate, checkable findings? | Versioned tasks, independent citation checks, rubric scores |
| Golden-case regression | Did repeated assistant tasks improve or regress? | Expected and actual outputs, judge dimensions, latency, run history |
| End-to-end workflow testing | Did the user receive the requested result? | Streamed events, actual tool actions, artifacts, UI observations, completion state |
| Component evaluation | Does a learned component improve its particular job? | Held-out classification or retrieval tests, replay comparisons, runtime parity |
| Human evaluation | What needed correction, and was it absorbed? | Ratings, corrected decisions, assistance records, reviewer findings |
| Data-quality evaluation | Is this material suitable to learn from? | Provenance, supported labels, contamination review, sensitive-content checks |

## Forge-Bench rubric

| Axis | What to inspect |
|---|---|
| Precision | Claims and citations are correct and checkable |
| Recall | Important known findings were found |
| Calibration | Confidence and stated limits match the evidence |
| Discipline | Constraints were followed during execution |
| Cost | Resource use is measured and interpreted against comparable work |

The original task families cover locating code sites, tracing cross-file state, identifying divergent behavior, resolving duplicate definitions, comparing guards, assessing refactoring impact, reasoning about shared objects, following move-only instructions, and handling long context.

The code snapshot is part of the task. Recheck the answer key when code changes; retire tasks whose premise is no longer true. Do not aggregate mismatched tasks into an overall model winner. The [leaderboard](LEADERBOARD.md) publishes a small historical score snapshot with those limits visible.

## Automated output evaluation

The implemented golden-case harness exercises code generation, tool use, arithmetic, explanation, file operations, structured output, and error handling. A model judge scores correctness, helpfulness, conciseness, and safety; run history supports regression comparisons.

Judge scores remain fallible. The current judge can emit neutral values when scoring fails, so a neutral score is not evidence of acceptance. Successful output generation also does not establish that a file or external action exists. Use artifact, runtime, and human checks for the claims that require them.

## Long-horizon episodes

The founder's structural planning and build cycles can span one to two days of sustained model collaboration. A cycle may include research, several proposed designs, rejected assumptions, implementation, tests, review, and corrections. This describes a development workflow, not a guarantee that every production task runs unattended for that duration.

For your own evaluation, preserve the trajectory:

1. Define the goal and acceptance conditions before work begins.
2. Record plan revisions and their reasons.
3. Identify the actual executor and the evidence it produced.
4. Record reviewer findings and human interventions.
5. Label completion only to the extent the evidence supports it.
6. Separate the training material from evaluation cases before training.

## Comparability and contamination

Record version, task, model, provider, date, assistance, and available resource measurements. Keep clean and blinded runs identifiable. Assisted work can demonstrate correction absorption; a run with readable answers cannot establish independent discovery.

For a new system, split related episodes together so neighboring turns from one conversation do not appear on opposite sides of train/test. Evaluate data eligibility independently of outcome: an accurately observed failure can be useful evidence, while a successful-looking but unverified answer can be unsuitable.

These are recommended practices for builders. They are not a claim that every historical Agent Forge record already satisfies the newest protocol.

## A compact example contract

The [offline example](../examples/evaluation_learning_loop.py) contains synthetic episodes with task family, actual runtime, verification status, outcome attribution, intervention status, and measured resources. It keeps an audit record for every episode but admits only qualifying outcomes to a public demonstration ledger.

Use it to understand the boundary, then define the richer contract your own application needs. It contains no real training rows, private answer keys, prompts, or production policy.
