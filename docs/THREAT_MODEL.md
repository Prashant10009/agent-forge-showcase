# Threat Model

## Assets to protect

- private production source and history;
- prompts, agent instructions, routing policy, evaluation material, and operational knowledge;
- credentials, provider configuration, quotas, endpoints, and infrastructure details;
- private user, project, session, trace, upload, and runtime data;
- the consistency of the Agent Forge brand and the accuracy of public claims.

## Threats and controls

| Threat | Control |
|---|---|
| A public repo is created from private Git history | Fresh repository with unrelated history |
| A second UI drifts from the real product | No-duplication test; repository links use the canonical website |
| Production code is copied as a “sample” | Documentation and responsibility maps only |
| Live tour source exposes authenticated API behavior | Commit screenshots and links, never the application bundle |
| Screenshots reveal private state | Capture only unauthenticated website and labeled sample-data tour surfaces |
| Credentials or local paths enter prose or examples | Boundary scanner, GitHub secret scanning, and push protection |
| Architecture detail reveals proprietary policy | Describe responsibilities and boundaries; withhold weights, thresholds, prompts, and algorithms |
| Marketing statements outrun evidence | Use public links, repository evidence, or dated read-only snapshots |
| Dependencies become stale or unsafe | Dependabot, dependency review, CodeQL, and protected branches |
| Brand fragments across public surfaces | Official mark and documented identity; one canonical product URL |

## Trust boundaries

This repository does not authenticate users, accept product data, connect to model providers, or call production APIs. Links cross into the separately operated Agent Forge website and application, each with its own runtime and security boundary.

## Review cadence

Every content change passes automated checks and code-owner review. Screenshots, codebase counts, architecture claims, and public links should be refreshed together when the product materially changes.
