import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("points to the existing product instead of duplicating it", async () => {
  const readme = await read("README.md");
  assert.match(readme, /https:\/\/myagentforge\.ai\//);
  assert.match(readme, /tour_factual\.html#demo/);
  assert.match(readme, /existing product tour/i);
  assert.match(readme, /does not rebuild them/i);
  assert.doesNotMatch(readme, /synthetic mission/i);
});

test("includes official brand and authentic public captures", async () => {
  const logoFiles = [
    "agent-forge-primary-stacked.svg",
    "agent-forge-horizontal-dark.svg",
    "agent-forge-horizontal-light.svg",
    "agent-forge-mark-16.svg",
    "agent-forge-mark-24.svg",
    "agent-forge-mark-36.svg",
    "agent-forge-mark-52.svg",
    "agent-forge-static-lockup.svg",
    "agent-forge-thinking.svg",
    "agent-forge-topbar.svg",
    "agent-forge-watermark.svg",
    "agent-forge-monochrome.svg"
  ];
  for (const file of logoFiles) {
    const logo = await read(`assets/brand/${file}`);
    assert.match(logo, /<svg/);
    assert.match(logo, /M44,8|FORGE/);
  }
  await assert.rejects(access(new URL("../assets/brand/agent_forge_logo_v3.svg", import.meta.url)));
  for (const file of [
    "assets/screenshots/website-hero.png",
    "assets/screenshots/website-home.png",
    "assets/screenshots/product-tour.png"
  ]) await access(new URL(`../${file}`, import.meta.url));
});

test("contains no duplicate website or demo implementation", async () => {
  for (const directory of ["site", "website", "demo"]) {
    await assert.rejects(access(new URL(`../${directory}`, import.meta.url)));
  }
});

test("includes a runnable provider-neutral public core", async () => {
  for (const file of [
    "pyproject.toml",
    "src/agent_forge_public/orchestrator.py",
    "src/agent_forge_public/routing.py",
    "src/agent_forge_public/governance.py",
    "src/agent_forge_public/dispatch.py",
    "src/agent_forge_public/cli.py",
    "src/agent_forge_public/contracts.py",
    "src/agent_forge_public/control.py",
    "src/agent_forge_public/control_plane.py",
    "src/agent_forge_public/execution.py",
    "src/agent_forge_public/manifests.py",
    "src/agent_forge_public/state.py",
    "src/agent_forge_public/workflow_graph.py",
    "examples/governed_run.py",
    "examples/control_plane_lab.py",
    "tests_python/test_governance_orchestrator.py",
    "tests_python/test_control_primitives.py",
    "tests_python/test_manifests_state.py",
    "tests_python/test_selection_execution.py",
    "tests_python/test_control_plane_workflow.py"
  ]) await access(new URL(`../${file}`, import.meta.url));

  const boundary = await read("docs/PUBLIC_BOUNDARY.md");
  assert.match(boundary, /provider-neutral public core/i);
  assert.match(boundary, /not production policy/i);
});

test("includes substantive engineering documentation", async () => {
  for (const file of [
    "docs/ARCHITECTURE.md",
    "docs/BRAND_IDENTITY.md",
    "docs/CODEBASE_MAP.md",
    "docs/PUBLIC_BOUNDARY.md",
    "docs/PUBLIC_CORE.md",
    "docs/PUBLIC_IMPLEMENTATION_MAP.md",
    "docs/SYSTEM_WALKTHROUGH.md",
    "docs/FAILURE_MODEL.md",
    "docs/THREAT_MODEL.md"
  ]) {
    const content = await read(file);
    assert.ok(content.length > 400, `${file} should be substantive`);
  }
});

test("documents and exposes the deep control-plane scenarios", async () => {
  const readme = await read("README.md");
  const core = await read("docs/PUBLIC_CORE.md");
  const controlPlane = await read("src/agent_forge_public/control_plane.py");
  assert.match(readme, /agent-forge-public lab all/);
  assert.match(core, /exact-action (approval )?manifest/i);
  assert.match(core, /tenant-scoped (context|state|memory)/i);
  assert.match(controlPlane, /class PublicControlPlane/);
  assert.match(controlPlane, /_terminalize_manifest/);
});
