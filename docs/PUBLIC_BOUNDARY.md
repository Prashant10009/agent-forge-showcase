# Public Boundary

This repository is a curated portfolio edition, not a mirror, fork, export, or deployment artifact of Agent Forge production.

## Allowed content

- Original public-showcase HTML, CSS, JavaScript, SVG, and documentation.
- Synthetic fixtures with explicit notices.
- High-level architecture and interface relationships.
- Generic reliability and governance patterns.
- Tests and CI checks written specifically for this repository.
- Brand assets created specifically for the public showcase.

## Forbidden content

- Files copied from private source trees unless independently reviewed and recorded as an approved public brand asset.
- Production application code or implementation-specific algorithms.
- Routing weights, thresholds, provider scoring, proprietary prompts, agent instructions, or evaluation answers.
- Secrets, credential-shaped values, live endpoints, account identifiers, emails, local user paths, hostnames, or infrastructure inventories.
- Chat history, builder logs, handoffs, incident records, telemetry, database files, backups, uploads, or caches.
- Customer, carrier, driver, vehicle, claim, loss-run, underwriting, financial, or personal data.
- Screenshots containing real sessions, users, documents, quotas, provider identities, or private project names.

## Synthetic data rules

1. Every structured fixture must identify itself as synthetic.
2. Paths use `/workspace/sample/` or similarly fictional namespaces.
3. Runtime names are functional aliases such as `reasoning-core`, not live provider/model inventory.
4. Timings are illustrative and are not presented as benchmarks.
5. Underwriting or structured-document demonstrations must visibly say `Synthetic demo data` and must not imply that a regulator supplied private records.

## Automated enforcement

`npm run check:boundary` fails on:

- forbidden directory and file patterns;
- private-repository names;
- common secret formats;
- Windows user paths;
- database, backup, archive, environment, log, or telemetry artifacts;
- unapproved binary assets.

Automation is a backstop, not the final authority. Publication also requires a complete tree review, image inspection, Git-history scan, and logged-out verification.

## License boundary

The MIT license applies only to files committed to this public repository. It grants no rights to private Agent Forge code, services, data, models, policies, prompts, or infrastructure.
