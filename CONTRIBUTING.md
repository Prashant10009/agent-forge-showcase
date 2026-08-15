# Contributing

Thanks for helping improve the Agent Forge public showcase.

## Start here

1. Read [PUBLIC_BOUNDARY.md](docs/PUBLIC_BOUNDARY.md).
2. Create a branch from `main`.
3. Keep fixtures synthetic and the site dependency-free unless a dependency has a clear, reviewed benefit.
4. Run `npm run check`.
5. Complete every item in the pull-request public-boundary checklist.

## Design contributions

- Preserve the graphite/amber visual system.
- Keep one obvious primary action per section.
- Use motion only to communicate hierarchy, state, or flow.
- Test keyboard access, mobile layout, and reduced-motion mode.
- Do not use real production screenshots or account data.

## Code contributions

- Prefer small, readable modules.
- Keep the demo deterministic and offline-capable.
- Add or update tests for state changes.
- Do not add analytics, remote fonts, trackers, provider clients, or production endpoints.

## Security

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).
