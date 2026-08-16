# Failure Model

The public core treats failure as part of the system contract. A run must finish as `completed`, `failed`, or `cancelled`; a missing response is never interpreted as success.

| Failure surface | Detection | Containment | Observable result |
|---|---|---|---|
| Missing capability | Eligibility filtering | Runtime excluded before dispatch | Candidate exclusion reason |
| Unavailable runtime | Health state | Runtime excluded | Candidate exclusion reason |
| Repeated runtime failures | Tenant-scoped circuit | Circuit opens; later work selects another runtime | Circuit state and attempt records |
| Recovery probe contention | Atomic half-open claim | One probe proceeds | Other callers see unavailable circuit |
| Transient adapter failure | Typed retryable error | Move to bounded compatible fallback | Failed attempt plus successful attempt |
| Permanent adapter failure | Typed non-retryable error | Stop fallback chain | Terminal failed run |
| Capacity saturation | Atomic capacity claim | Attempt fails without oversubscription | Capacity error attempt |
| Budget overrun risk | Pre-dispatch reservation | Dispatch rejected before spend | Budget error and released reservation |
| Operator cancellation | Cooperative token | Checked before and inside execution boundaries | Cancelled terminal event |
| Deadline expiry | Monotonic deadline | Same cancellation path | Cancelled result with deadline reason |
| Approval payload change | Canonical exact comparison | Claim rejected | Action-mismatch error |
| Approval theft | Ownership comparison | Approve/claim rejected | Tenant, session, run or scope error |
| Approval replay/race | Atomic state transition | One claimant; terminal tombstone blocks reuse | Replay error |
| Tool validation failure | Registered typed contract | Manifest completes unsuccessfully | Failed action capability and run |
| Missing expected artifact | Post-action verification | Run does not complete successfully | Verification failure |
| Cross-tenant artifact read | Ownership check at retrieval | Read denied | Tenant-boundary error |
| Workflow cycle | Graph construction | Workflow never starts | Invalid-workflow error |
| Dependency failure | Prior node outcome | Downstream skip or explicit continuation | Dependency context on node result |
| Late completion/event | Terminal-state guard | Mutation rejected | Terminal-event or transition error |

## Terminal liveness

The run journal permits exactly one terminal event. The state store rejects transitions after a terminal state. The manifest follows its own lifecycle and is explicitly completed, rejected or expired. If execution fails before a tool claim, the approved capability is rejected; if it fails after a claim, the capability completes unsuccessfully.

## Cancellation boundary

Cancellation is cooperative because abrupt thread termination can corrupt shared state. Tokens are checked before runtime dispatch, by adapters, before each tool action, and before workflow waves. The public implementation makes those checks visible and testable.

## Distributed-system limit

This offline edition demonstrates invariants with locks and in-memory state. It does not claim that process-local locks replace transactional storage, leases, distributed queues or idempotency infrastructure. Those service choices are intentionally outside the publication boundary.
