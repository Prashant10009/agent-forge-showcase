# Engineering Notes

## Why the public edition is documentation-first

Publishing a partial production tree creates two bad outcomes: accidental disclosure and a misleading, broken repository. This edition instead publishes original demo code, system relationships, safety boundaries, and testable product behavior.

That choice gives reviewers useful signal:

- product architecture is legible;
- execution state is interactive;
- governance is visible;
- testing and release discipline are inspectable;
- proprietary implementation remains private.

## Why the demo is deterministic

A portfolio reviewer should not need provider accounts, API keys, local models, GPUs, databases, or a specific cloud environment. The demo engine maps a small set of synthetic task shapes to fictional runtime aliases and produces a stable trace.

Determinism makes the interface easy to test and prevents fake network activity from being mistaken for product proof.

## Why approval is modeled separately from routing

Model selection answers who should reason about a task. It does not answer whether a proposed action is authorized. The UI therefore places the approval gate after route and tool scoping, and before the verified terminal result.

## Why the public checks inspect repository content

Conventional CI can be green while a repository leaks data. This project adds a separate public-boundary check that rejects unsafe path classes and credential-shaped strings. The check is intentionally conservative and is complemented by manual review.

## Visual system

The public experience preserves Agent Forge's visual DNA without copying production UI code:

- near-black, layered surfaces;
- warm amber for energy, routing, and selected state;
- mono typography for system metadata;
- asymmetrical editorial composition;
- motion only when it communicates state or flow;
- reduced-motion support.
