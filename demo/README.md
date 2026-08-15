# Synthetic Demo

The demo uses fictional task shapes, runtime aliases, paths, timings, and results. It never connects to Agent Forge production or third-party model providers.

- `engine.mjs` contains the deterministic public state model.
- `fixtures/synthetic-mission.json` documents a representative synthetic mission payload.
- `site/app.js` presents the state transitions and approval boundary.

Run `npm test` to verify route determinism and lifecycle ordering.
