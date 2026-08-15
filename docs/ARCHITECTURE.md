# Architecture

Agent Forge treats AI execution as a governed system rather than a single model call. This document describes the public architecture at the level needed to evaluate design judgment while withholding production source, policies, prompts, routing weights, infrastructure, and data.

## Design goals

1. Route each task to an appropriate runtime instead of binding the product to one provider.
2. Make consequential tool use visible and interruptible.
3. Keep state boundaries explicit: request, session, project, outcome, and durable memory are different concerns.
4. Produce evidence for why an action occurred and whether the result was verified.
5. Keep runtime adapters replaceable and degrade predictably when a provider is unavailable.

## Four layers

### 1. Experience

The experience layer turns system state into useful product surfaces:

- mission-oriented chat;
- execution graph and trace;
- action manifest and approval controls;
- project and file context;
- structured-data workspace concepts;
- runtime and health visibility.

Its responsibility is not merely presentation. It preserves the distinction between proposed work, approved work, running work, and verified work.

### 2. Orchestration

The orchestration layer coordinates a request through bounded stages:

```text
intake → context → planning → routing → tool dispatch → post-processing → verification
```

Each stage accepts and returns an explicit state contract. Production contains richer policy and recovery behavior; the public edition demonstrates only the stage relationships.

### 3. Intelligence and governance

This layer answers two different questions:

- **Intelligence:** Which runtime or specialist best fits the task under current constraints?
- **Governance:** What is the system allowed to do, and what needs human approval?

Keeping those questions separate prevents model confidence from becoming execution authority. A strong route can still be stopped at a policy boundary.

Public concepts include:

- task-shape and capability fit;
- runtime-health awareness;
- outcome signals;
- explicit approval manifests;
- multi-perspective review;
- durable memory boundaries.

The production weights, thresholds, prompts, and adjudication policies are not public.

### 4. Replaceable runtimes

Provider clients, local runtimes, remote runtimes, protocol tools, vector stores, and telemetry backends sit behind adapters. This isolates the product model from provider churn and enables health-aware fallback.

The public repository names the interfaces and relationships but includes no production credentials, endpoint inventory, quota data, or operational configuration.

## Request lifecycle

The synthetic mission in this repository illustrates the lifecycle:

1. **Intent intake** assigns a public demo task shape.
2. **Context assembly** attaches four synthetic signals.
3. **Dynamic route** selects a fictional runtime alias and explains the fit.
4. **Tool scope** creates a read/propose-only manifest against demo paths.
5. **Approval boundary** requires a human choice.
6. **Verification** records the terminal result.

The demo is deliberately deterministic so reviewers can test state transitions without paid APIs or network variability.

## Reliability posture

Agent Forge's public architecture reflects several production-grade principles:

- an edge/proxy health response is not treated as proof that the application is serving;
- terminal states are explicit and cannot be inferred from silence;
- blocking provider operations require bounded time and cancellation behavior;
- write authority is not granted by model selection;
- verification attaches to the artifact and behavior that matter, not only to a generated report;
- observability records stage transitions, not just final text.

## Security and privacy boundary

This diagram is the complete public dependency model:

![Agent Forge public architecture](../assets/diagrams/architecture.svg)

Anything not represented here should be assumed private. See [PUBLIC_BOUNDARY.md](PUBLIC_BOUNDARY.md) and [THREAT_MODEL.md](THREAT_MODEL.md).
