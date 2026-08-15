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
  const logo = await read("assets/brand/agent_forge_logo_v3.svg");
  assert.match(logo, /<svg/);
  assert.match(logo, /ff4500/i);
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

test("includes substantive engineering documentation", async () => {
  for (const file of [
    "docs/ARCHITECTURE.md",
    "docs/BRAND_IDENTITY.md",
    "docs/CODEBASE_MAP.md",
    "docs/PUBLIC_BOUNDARY.md",
    "docs/THREAT_MODEL.md"
  ]) {
    const content = await read(file);
    assert.ok(content.length > 400, `${file} should be substantive`);
  }
});
