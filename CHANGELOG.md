# Changelog

All notable changes to the public showcase are documented here.

## [Unreleased] - 2026-11-01

### Added

- A one-page turn diagram (`docs/diagrams/turn-overview.svg`, editable `.excalidraw` source) and a "One turn, end to end" README section.
- "Added between September and November 2026" in the production section: plans that survive, agent trees, typed decisions with in-house students, the trained encoder, per-call accounting, runtime verification, re-attachable turns, document reading, and surfaces.
- `docs/LEARNING_SYSTEMS.md`, checked against the November architecture.
- Pattern guides carried over from the closed October draft: how Agent Forge works, behaviour evaluation, the evaluation framework, the historical Forge-Bench leaderboard, build your own, and the runnable evaluation-to-learning example with its tests.
- A November 2026 codebase snapshot beside the August one.

### Not carried over

- The October draft's retrieval-reranking claims, which did not match production.

## [0.4.0] - 2026-08-15

### Added

- Full provider-neutral control-plane vertical slice with typed lifecycle contracts.
- Evidence-aware routing, tenant circuits, capacity claims, deadline cancellation, atomic budget reservations, and bounded fallbacks.
- Exact-action approval manifests bound to tenant, session, run, and scope with concurrent-claim and replay protection.
- Tenant-scoped memory and checkpoints, immutable content-addressed artifacts, multi-perspective review, and topology-preserving workflow execution.
- Four deterministic system lab scenarios plus system walkthrough, failure model, and public implementation map.
- Expanded Python suite from 14 to 64 tests, including concurrency, isolation, denial, degradation, and terminal-liveness cases.

### Changed

- Reframed the README around executable engineering evidence and verified production scale.
- Updated the private codebase snapshot after a fresh read-only inventory.

## [0.3.0] - 2026-08-15

### Added

- Provider-neutral Python orchestration core with deterministic runtime adapters.
- Explained capability routing, explicit approval gates, replay protection, traces, and checkpoints.
- Dependency-aware parallel task dispatch, CLI commands, examples, and unit tests.
- Public-core architecture and substitution documentation.

### Changed

- Added Python verification to CI and the engineering-dossier build artifact.
- Updated the README to lead reviewers from the existing product surfaces into runnable code.

## [0.2.0] — 2026-08-15

### Changed

- Reframed the repository as a GitHub-native engineering dossier.
- Removed the duplicate portfolio UI and synthetic mission demo.
- Adopted the official Agent Forge mark and documented brand identity.
- Added authentic captures of the existing website and product tour.
- Added a verified private-codebase map and point-in-time inventory.
- Changed GitHub Pages to redirect to the canonical website.
- Strengthened the public-boundary gate against duplicate UI, API wiring, personal email, and local endpoints.

## [0.1.0] — 2026-08-15

### Added

- Original interactive synthetic orchestration cockpit.
- Public four-layer architecture and engineering narrative.
- Explicit approval-boundary demonstration.
- Deterministic demo engine and tests.
- Repository content boundary scanner and local-link validator.
- GitHub Actions for CI, CodeQL, dependency review, Pages, and releases.
- Contribution, security, issue, pull-request, and ownership controls.
