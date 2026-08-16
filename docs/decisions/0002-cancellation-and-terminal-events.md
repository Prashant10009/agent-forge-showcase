# 0002: Require cooperative cancellation and terminal events

Status: accepted

## Context

Abruptly terminating shared work can leave reservations, manifests, subprocesses or user-visible state unresolved. Conversely, an ended stream without a terminal signal leaves the caller unable to distinguish success from transport failure.

## Decision

Cancellation uses a token checked at execution boundaries. Run and stream journals allow exactly one terminal event. Inactivity after visible output preserves that output in a terminal result; inactivity without output becomes incomplete; early EOF remains an error.

## Consequences

Workers must cooperate with cancellation, and every path must close its state explicitly. The extra checks create a stronger liveness contract and prevent silent success assumptions.

Public evidence: `control.py`, `events.py`, `streaming.py`, and their tests.
