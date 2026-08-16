import { cp, mkdir, rm, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

for (const directory of ["assets", "docs", "examples", "src", "tests_python"]) {
  await cp(resolve(root, directory), resolve(dist, directory), { recursive: true });
}

for (const file of [
  "README.md",
  "LICENSE",
  "TRADEMARKS.md",
  "SECURITY.md",
  "CHANGELOG.md",
  "CITATION.cff",
  "pyproject.toml"
]) await cp(resolve(root, file), resolve(dist, file));

await writeFile(resolve(dist, "manifest.json"), `${JSON.stringify({
  name: "Agent Forge Engineering Dossier",
  version: "0.4.0",
  website: "https://myagentforge.ai/",
  tour: "https://myagentforge.ai/tour_factual.html#demo",
  publicCoreIncluded: true,
  productionSourceIncluded: false
}, null, 2)}\n`);

console.log("Built public engineering dossier in dist/");
