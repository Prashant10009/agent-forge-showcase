# Forge-Bench leaderboard

A historical, task-level snapshot of Agent Forge's evaluation record. It helps explain the methodology and observed strengths; it is not a current universal model ranking or a live benchmark feed.

## Recorded results: August 11, 2026

All rows below were recorded under Forge-Bench v1. Each row represents one task result, not repeated trials or a confidence interval.

| Model | Task | Recorded score | Evidence and interpretation |
|---|---|---:|---|
| Kimi K2.7-code | T2: cross-file state | 94 / 100 | Citations independently checked; benchmark worktree blinded |
| Kimi K2.7-code | T4: duplicate definitions | 95 / 100 | Live and inactive definitions verified against pinned code |
| Kimi K2.7-code | T7: shared-object semantics | 95 / 100 | Object mutation and rebinding distinguished and verified |
| MiniMax M3 | T5: inconsistent guards | 98 / 100 | Independently scored; blinded worktree; separate +5 bonus omitted; resource estimates approximate |
| MiniMax M3 | T6-labelled: structural analysis | 99 / 100 | Independently scored; inherited blinding; recorded task differs from the canonical T6 prompt |

The Kimi task values above are the recorded task scores. The independent whole-run assessment was 93/100 and the weighted total remained unset. These are different assessments; averaging the task rows must not silently replace the independent review.

The MiniMax T6-labelled record describes structure and import relationships, while the canonical T6 prompt concerns source-coupled tests. Its task-label mismatch is disclosed rather than treated as an equivalent comparison.

## What these results tell us

The evaluated models demonstrated different useful behaviors on actual engineering work: cross-file tracing, precise verification, and explicit uncertainty. The broader live-work record includes GLM, DeepSeek, Qwen, Nemotron, Kimi, and MiniMax, with findings, corrections, and reviewer mistakes retained.

Different tasks, contexts, assistance, and resource measurement prevent a defensible overall ordering from this sample. Live-work evaluations remain valuable without being presented as controlled benchmark wins. There is no claim here that Agent Forge outperforms a flagship model on equivalent tasks.

## Provenance

The maintainer's dated benchmark specification, consolidated ledger, and per-run records were checked on October 5, 2026. Only the model names, task descriptions, recorded scores, dates, and interpretation notes above are included in this public snapshot. Raw task answers, code citations, private run records, and answer keys are not distributed. These scores are reported historical records, not independently reproducible public benchmark results.

Future additions should identify task/version, sample count, independent review, assistance, contamination status, resource measurement, and whether the result supersedes an older score.

See the [evaluation framework](EVALUATION_FRAMEWORK.md) to build a comparable evaluation for your own system, or run the [synthetic learning example](../examples/evaluation_learning_loop.py) to inspect how acceptance can precede routing feedback.

## Component evidence is a separate comparison

See [behavior evaluation](BEHAVIOR_EVALUATION.md) for October 3 decision-head measurements: 83/85 versus 78/85 on trivial-message classification, and 70/75 versus 67/75 on council selection. The latter improves false council calls while missing more needed councils. Both candidates remain disabled. Those results, retrieval measurements, and watcher experiments answer different questions from the model task scores above; they do not form one combined ranking.
