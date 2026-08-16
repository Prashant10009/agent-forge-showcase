# 0003: Carry tenant identity through every state boundary

Status: accepted

## Context

Globally convenient identifiers such as run IDs, artifact IDs or vector record IDs are not sufficient authorization. Filtering only after a broad lookup risks cross-tenant access and identifier collision.

## Decision

Tenant identity participates in state keys and access checks for memory, checkpoints, run state, budgets, circuits, artifacts, outcome evidence and task vectors. Cross-tenant direct reads fail rather than returning an empty or partially filtered object.

## Consequences

Callers must carry identity throughout the lifecycle and storage adapters must enforce it at query time. The public implementation uses in-memory structures, but the contract applies equally to durable stores.

Public evidence: `state.py`, `control.py`, `task_state.py`, and their tests.
