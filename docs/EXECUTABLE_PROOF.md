# Executable proof: roles, routing, and bounded learning

This page demonstrates one central Agent Forge claim with runnable, provider-neutral code:

> **An agent owns a responsibility; a runtime is a replaceable execution resource.**

The demonstration is intentionally small and deterministic. It is not a copy of the private production engine and does not disclose production prompts, model/provider inventory, routing weights, thresholds, learned parameters, telemetry, endpoints, or deployment configuration.

## Run it

From the repository root:

```bash
python -m pip install -e .
python examples/role_routing_learning_demo.py
```

The output is JSON so the decision path is inspectable rather than hidden behind a UI.

## What the demo does

1. Creates a **coding agent role** with public capability requirements.
2. Evaluates three synthetic execution resources.
3. Excludes a research-oriented runtime because it lacks the coding capability required by the role.
4. Selects one eligible coding runtime using the existing public demonstration router.
5. Records deliberately obvious, synthetic outcome evidence: repeated failures for the initially selected runtime and repeated successes for another compatible runtime.
6. Routes a second coding task.
7. Shows that the selected runtime changes while the **agent role remains `coding`**.

The point is not that these particular synthetic scores are intelligent. The point is that the system contracts keep **role identity**, **runtime eligibility**, **runtime selection**, and **outcome evidence** separate and inspectable.

## Public role layer

`src/agent_forge_public/roles.py` defines a small provider-neutral catalog for demonstration:

- general
- coding
- research
- analysis
- document
- vision

Each role contributes capability requirements and descriptive responsibility metadata. A role does **not** name a provider or model and does not directly choose a runtime.

## Routing explanation

`src/agent_forge_public/routing_explain.py` converts the already-public `RoutingPlan` into an audit-friendly view containing:

- selected runtime;
- ranked eligible candidates;
- fallback order;
- public demonstration score components;
- explicit exclusion reasons;
- the public policy label.

This explanation layer does not infer private production logic. It only exposes information already present in the public reference contracts.

## Bounded outcome evidence

The existing public `OutcomeLedger` stores tenant-scoped success/failure evidence. The public demonstration router uses the resulting reliability signal as one bounded component of selection.

The learning demo intentionally makes the evidence extreme so the effect is obvious and deterministic. Production behavior is **not** represented by the number of samples, scoring values, or update pattern used in this example.

## Tests

`tests_python/test_roles_and_learning.py` verifies that:

- applying a role does not mutate the original request;
- a role adds capability requirements without binding a runtime;
- incompatible runtimes receive explicit exclusion reasons;
- synthetic outcome evidence can change the selected runtime;
- the agent role remains unchanged when the runtime changes.

Run the complete Python contract suite with:

```bash
python -m unittest discover -s tests_python -v
```

## Publication boundary

This executable proof is independently authored against the public contracts. It intentionally avoids production package names, provider identities, routing feature construction, thresholds, prompts, weights, learned state, private traces, or customer/session data.

For the broader architecture, see [ARCHITECTURE.md](ARCHITECTURE.md), [PRODUCTION_CAPABILITIES.md](PRODUCTION_CAPABILITIES.md), and [PUBLIC_BOUNDARY.md](PUBLIC_BOUNDARY.md).
