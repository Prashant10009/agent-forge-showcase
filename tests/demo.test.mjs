import test from "node:test";
import assert from "node:assert/strict";
import { buildSyntheticTrace, chooseDemoRoute, publicBoundarySummary, DEMO_NOTICE } from "../demo/engine.mjs";

test("demo route is deterministic and uses a fictional alias", () => {
  const first = chooseDemoRoute("audit");
  const second = chooseDemoRoute("audit");
  assert.deepEqual(first, second);
  assert.equal(first.selected, "reasoning-core");
  assert.match(first.reason, /review boundary/i);
});

test("unknown task shapes fail closed to the public audit route", () => {
  assert.deepEqual(chooseDemoRoute("unknown"), chooseDemoRoute("audit"));
});

test("trace preserves the governance boundary before verification", () => {
  const trace = buildSyntheticTrace("audit");
  assert.deepEqual(trace.map((stage) => stage.id), ["intent", "context", "route", "tools", "approval", "verify"]);
  assert.ok(trace.findIndex((stage) => stage.id === "approval") < trace.findIndex((stage) => stage.id === "verify"));
});

test("public boundary names included and excluded concerns", () => {
  const boundary = publicBoundarySummary();
  assert.ok(boundary.included.includes("Synthetic UX"));
  assert.ok(boundary.excluded.includes("Production source"));
  assert.match(DEMO_NOTICE, /synthetic/i);
  assert.match(DEMO_NOTICE, /no production data/i);
});
