# 0001: Separate selection from authority

Status: accepted

## Context

A runtime can be technically capable of performing work without being authorized to execute the resulting actions. Combining routing and permission would let a score or fallback decision accidentally broaden authority.

## Decision

Routing produces an explained, capability-compatible execution plan. A separate manifest captures the exact ordered action payload and binds it to tenant, session, run and approval scope. Consequential actions pause for approval and the approved capability can be claimed once.

## Consequences

Runtime replacement does not change what actions were approved. A changed payload, different owner, replay, expiry or concurrent second claimant is rejected. This adds lifecycle state, but makes authority observable and testable.

Public evidence: `selection.py`, `manifests.py`, `actions.py`, and their tests.
