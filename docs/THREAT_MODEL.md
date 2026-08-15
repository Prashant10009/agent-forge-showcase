# Threat Model

## Assets to protect

- private production source and Git history;
- proprietary routing and governance policy;
- prompts, agent instructions, and evaluation material;
- credentials, provider inventory, quotas, and infrastructure details;
- founder, user, customer, and runtime data;
- the accuracy of public claims.

## Threats and mitigations

| Threat | Mitigation |
|---|---|
| Private history is exposed by repurposing an old repository | Create a new repository with one fresh root commit |
| Runtime data is copied with source | Allowlist-only construction; forbidden-path check |
| Secrets appear in examples | Placeholder-free synthetic demo; secret-pattern scan |
| Screenshots reveal real sessions or identities | Capture only the standalone synthetic site; inspect every image |
| High-level documentation reveals implementation policy | Describe responsibilities and boundaries, not weights, prompts, or algorithms |
| Green proxy health is misrepresented as application health | Document and test application-level verification separately |
| Public demo sends data to third parties | No analytics, external fonts, provider calls, forms, or remote APIs |
| Dependencies introduce supply-chain risk | Zero runtime dependencies; Dependabot and CodeQL for repository tooling |
| Marketing claims drift beyond evidence | Link claims to public code, tests, or clearly label them architectural |

## Out of scope

This repository is not a deployable production service and does not accept untrusted data, authenticate users, store documents, or call model providers.

Security reports about this showcase should follow [SECURITY.md](../SECURITY.md). Reports about private Agent Forge services should not include sensitive evidence in a public issue.
