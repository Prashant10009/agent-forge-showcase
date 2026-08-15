# Public Boundary

This repository is an engineering dossier, not a source release or parallel implementation.

## Included

- product positioning already published at `myagentforge.ai`;
- authentic captures of the public website and labeled interactive tour;
- the official Agent Forge logo asset;
- high-level architecture and responsibility maps;
- point-in-time codebase counts and package-group descriptions;
- publication tests, link checks, leak scanning, GitHub workflows, and release metadata;
- contribution, security, privacy, terms, and trademark notices for this repository.

## Private by design

- production application source and Git history;
- authenticated application bundles and API wiring;
- prompts, agent instructions, routing weights, thresholds, and policy logic;
- credentials, provider inventories, quotas, internal endpoints, and deployment configuration;
- database schemas, private sessions, projects, traces, uploads, logs, and evaluation data;
- operational runbooks, incident evidence, and internal handoff documents.

## No duplication rule

The public repository must not contain a `site`, `website`, or `demo` implementation. The existing website and tour remain the product surfaces, and repository metadata links directly to them.

## Visual provenance

Committed screenshots must meet all of these conditions:

1. captured from the public website or its explicitly labeled sample-data tour;
2. contain no authenticated user session, private project, personal record, or production trace;
3. visually reviewed before publication;
4. stored only under `assets/screenshots/` and named for the public surface shown.

## Automated enforcement

`scripts/check-public-boundary.mjs` rejects:

- forbidden artifact directories and archive/database formats;
- local workspace paths and private handoff material;
- credential-shaped strings and private keys;
- personal email addresses;
- embedded `/api/` fetch calls, bearer-token wiring, and local service endpoints;
- unapproved binary files.

The scanner is a backstop, not proof by itself. Every pull request also requires human review of prose, images, diffs, and provenance.

## Publication checklist

- [ ] The change explains the product without copying private implementation.
- [ ] Every claim is public, verified, or explicitly labeled as a point-in-time snapshot.
- [ ] Images come from an approved public surface.
- [ ] No duplicate product interface or tour was introduced.
- [ ] `npm run check` passes.
- [ ] The pull-request boundary checklist is complete.
