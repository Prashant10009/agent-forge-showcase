# Executable proof: control plane, configured workers, and runtime selection

This page demonstrates a narrower and more accurate Agent Forge claim with runnable,
provider-neutral code:

> **Agent Forge separates control-plane subsystems, reusable configured specialist workers, and the model/runtime resources used for execution.**

The public implementation is intentionally small and deterministic. It is not a copy
of the private production engine and does not disclose production prompts, the exact
worker inventory, provider/model inventory, routing feature construction, weights,
thresholds, learned parameters, telemetry, endpoints, or deployment configuration.

## Verified architecture boundary

Before this public proof was written, the production repository was checked read-only
against multiple independent sources for each architectural claim.

At a safe public level, production contains distinct responsibilities for:

- **Orchestrator** — a Python control system that owns the request lifecycle and wires
  routing, memory, Trimurti, tools, and worker creation.
- **Trimurti** — a Python deliberation subsystem with per-request and background
  operation, memory, sentinels, and pipeline components.
- **Sentinel gates** — validation/gating machinery at selected control boundaries.
- **Karma** — monitoring plus outcome/capability evidence used by routing and system
  health logic.
- **RTA** — a runtime-state/decision subsystem with backend lifecycle, flow/capacity,
  and strategy components.
- **Configured specialist workers** — reusable configured workers instantiated and
  dispatched for specialist work.
- **Execution runtimes** — replaceable model/backend resources used to perform
  computation.

These are not represented as subclasses of one universal public `Agent` abstraction.
The executable proof intentionally preserves those boundaries.

## Run it

From the repository root:

```bash
python -m pip install -e .
python examples/worker_runtime_learning_demo.py
```

The output is JSON so the decision path is inspectable rather than hidden behind a UI.

## What the demo does

1. Emits the independently authored public topology showing the distinct control,
   configured-worker, and execution layers.
2. Creates one **synthetic coding worker template** with public capability requirements.
3. Evaluates three synthetic execution runtimes.
4. Excludes a research-oriented runtime because it lacks the coding capability required
   by that worker responsibility.
5. Selects one eligible runtime using the existing public demonstration router.
6. Records deliberately obvious synthetic outcome evidence: repeated failures for the
   initially selected runtime and repeated successes for another compatible runtime.
7. Routes a second coding task.
8. Shows that the configured worker responsibility remains `coding` while the selected
   runtime changes.

The point is not that these synthetic scores reproduce production intelligence. They do
not. The point is that the public contracts visibly separate **worker responsibility**,
**runtime eligibility**, **runtime selection**, and **outcome evidence** while keeping
control-plane systems outside the worker abstraction.

## Public configured-worker layer

`src/agent_forge_public/worker_templates.py` defines a small synthetic catalog used only
for the public demo. The names in that catalog are broad capability examples, not a
copy of the private configured worker inventory.

Each template contributes capability requirements and responsibility metadata. A
worker template does **not** name a provider/model and does not directly choose an
execution runtime.

## Public topology layer

`src/agent_forge_public/system_topology.py` records the high-level component boundaries
that were independently verified before publication. It is not a production package
map. It exists primarily to prevent a misleading simplification where Orchestrator,
Trimurti, Karma, RTA, sentinels, configured workers, and runtimes are all treated as the
same kind of object.

## Routing explanation

`src/agent_forge_public/routing_explain.py` converts the already-public `RoutingPlan`
into an audit-friendly view containing:

- selected runtime;
- ranked eligible candidates;
- fallback order;
- public demonstration score components;
- explicit exclusion reasons;
- the synthetic worker responsibility;
- the public policy label.

This explanation layer does not infer private production logic. It only exposes
information already present in the public reference contracts.

## Bounded outcome evidence

The existing public `OutcomeLedger` stores tenant-scoped success/failure evidence. The
public demonstration router uses the resulting reliability signal as one bounded
component of selection.

This is a deliberately simple analogue used to demonstrate the architecture. It should
not be read as a specification of Karma, which is a broader private production
subsystem with monitoring, health, capability evidence, and routing integration.

Likewise, this public demo does not reproduce RTA. The private RTA subsystem has its own
runtime-state and decision machinery. The public example merely shows that runtime
state/evidence can remain separate from worker identity.

## Tests

`tests_python/test_worker_runtime_separation.py` verifies that:

- the public topology does not classify Orchestrator, Trimurti, Sentinels, Karma, or
  RTA as generic workers;
- applying a worker template does not mutate the original request;
- a configured worker responsibility adds capability requirements without binding a
  runtime;
- incompatible runtimes receive explicit exclusion reasons;
- synthetic outcome evidence can change the selected runtime;
- the configured worker responsibility remains unchanged when the runtime changes.

Run the complete Python contract suite with:

```bash
python -m unittest discover -s tests_python -v
```

## Publication boundary

This executable proof is independently authored against public contracts and verified
architectural responsibilities. It intentionally avoids production source structure,
private worker definitions, prompt text, provider identities, exact routing feature
construction, thresholds, weights, learned state, internal traces, or customer/session
data.

For the broader architecture, see [ARCHITECTURE.md](ARCHITECTURE.md),
[PRODUCTION_CAPABILITIES.md](PRODUCTION_CAPABILITIES.md), and
[PUBLIC_BOUNDARY.md](PUBLIC_BOUNDARY.md).
