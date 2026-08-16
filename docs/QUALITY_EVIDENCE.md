# Quality Evidence

This matrix ties public engineering claims to executable evidence. It is intentionally about invariants rather than private implementation breadth. All fixtures are deterministic and synthetic; no production trace, account, prompt, provider, endpoint, weight, threshold or customer record is included.

## Control-plane claims

| Claim | Public implementation | Executable evidence |
|---|---|---|
| One supported orchestration path | `PublicControlPlane`, CLI and scenarios | `test_control_plane_workflow.py`; CLI `lab all` |
| Selection is separate from authority | Evidence router followed by exact-action manifest | `test_selection_execution.py`; `test_manifests_state.py` |
| Approval is owner-bound and single-use | Tenant/session/run/scope identity plus atomic claim | Ownership, payload-mismatch, replay and race tests |
| Invalid rejection cannot destroy valid authority | Ownership validation occurs before pending-run removal | `test_wrong_owner_cannot_destroy_pending_run` |
| Tenant state is isolated at access time | Tenant-qualified memory, checkpoints, budgets, artifacts and vectors | Cross-tenant state, budget, artifact and task-vector tests |
| Capacity is not runtime failure | Capacity fallback does not change circuit or outcome evidence | `test_capacity_contention_falls_back_without_poisoning_health` |
| Cost is bounded before execution | Atomic reservation, actual-cost commit and exception release | Budget and execution tests |
| Completion requires real deliverables | Stored bytes, digest, size and expected logical names are verified | Artifact integrity and governed-run tests |
| Streams cannot disappear silently | Partial-preserving cutoff, incomplete empty stall, required terminal | `test_streaming.py` |
| Dependency work preserves topology | Cycle rejection, parallel waves and explicit failure context | Workflow tests in `test_control_plane_workflow.py` |
| Protocol calls remain capability-bound | Registered neutral adapter plus declared capability envelope | `test_protocols.py` |
| Similarity retrieval preserves its contract | Tenant, named space, dimension and finite-value validation | `test_task_state.py` |

## Repository claims

| Claim | Enforcement |
|---|---|
| No duplicate product website | Repository tests reject `site`, `website` and `demo` implementation directories |
| No production connection | Public-boundary scan rejects API wiring, local endpoints, credential patterns and private path classes |
| Brand continuity | Repository tests require the official exported logo family and authentic public captures |
| Supported Python versions | CI executes the core on Python 3.11 and 3.12 |
| Static security analysis | CodeQL analyzes both Python and JavaScript/TypeScript |
| Reproducible dossier | Link checks, boundary scan, tests and dossier build run on every pull request |
| Release integrity | Tagged dossier archives publish a SHA-256 checksum alongside the archive |

## Review path

1. Read the [sanitized governed trace](../examples/governed_trace.json).
2. Run `agent-forge-public lab all` to reproduce the four deterministic paths.
3. Run `python -m unittest discover -s tests_python -v` for the 72 contract tests.
4. Run `npm run check` for repository, boundary, link and dossier verification.
5. Read the [architecture decisions](decisions/README.md) to understand why the boundaries exist.

Passing tests demonstrate the public model exactly as documented. They do not claim production equivalence, disclose production policy, or substitute for the private system's deployment and service-level verification.
