# System Walkthrough

This walkthrough follows one consequential request through the public control plane. It is a deterministic simulation of system responsibilities, not a description of private algorithms.

## 1. Intake has an ownership envelope

Every request begins with a `RunIdentity`: run, tenant, session, and approval scope. That identity is carried into events, memory, checkpoints, manifests, artifacts, circuit state and runtime evidence. It prevents a globally valid identifier from becoming cross-tenant authority.

## 2. Classification produces evidence, not a magic label

The classifier returns required and preferred capabilities plus the terms that led to the classification. The router consumes capabilities, not prose labels. This keeps classification inspectable and runtime matching typed.

## 3. Context is filtered before use

The state store filters memory by tenant first and optionally by session. Checkpoints use a tenant-and-run key. Artifact reads re-check tenant ownership even when the caller already has an artifact identifier.

## 4. Review and routing answer different questions

Review asks whether the requested work may proceed to planning and what verification or preservation obligations apply. Routing then asks which runtime is eligible and preferable.

The public router evaluates:

- required and preferred capabilities;
- declared health and reliability;
- tenant-specific circuit state;
- observed tenant/runtime outcomes;
- tool support for consequential actions;
- normalized latency and cost.

Every candidate stays in the result with either score components or explicit exclusion reasons.

## 5. The action list becomes an exact capability

The planner produces typed actions. The manifest registry canonicalizes their ordered payload and stores a fingerprint. Approval is accepted only for the matching tenant, session, run and approval scope.

At execution time the tool executor submits the action list again. A byte-equivalent canonical representation must match the captured manifest. The claim is atomic, so simultaneous callers cannot both consume approval. Completed, rejected and expired manifests act as tombstones against replay.

## 6. Execution is bounded

Before dispatch, the executor reserves the maximum estimated cost of the bounded route chain. Each attempt checks cancellation and deadline, claims runtime capacity, consults the circuit breaker, invokes a narrow adapter, and records outcome evidence.

A retryable failure may move to the next compatible runtime. A permanent failure stops the chain. Success commits actual cost; exceptions release the reservation. Runtime success still does not mean run completion.

## 7. Tools and artifacts remain governed

Only the claimed manifest can reach tool handlers. The included handlers are safe local demonstrations. Created artifacts are content-addressed, immutable references whose identifiers include tenant and logical-name context.

## 8. Verification closes the run

The control plane checks non-empty runtime output, action success and expected artifact count. Only then does it append conversation memory, save a checkpoint, record completion and emit the terminal event.

Failure and cancellation also terminalize any pending or executing action manifest. This prevents an orphaned approval from surviving the run that created it.

## 9. Graph work preserves topology

For decomposed work, `WorkflowGraph` rejects unknown dependencies, duplicate nodes, self-dependencies and cycles. The scheduler runs only nodes in the current ready wave. Downstream nodes are skipped with dependency context unless they explicitly opt into continuation.

The result is a small but real control plane: its complexity comes from explicit contracts across failure, authority, concurrency, state and evidence—not from counting model calls.
