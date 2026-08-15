import { cp, mkdir, rm, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

for (const directory of ["assets", "demo", "docs", "site"]) {
  await cp(resolve(root, directory), resolve(dist, directory), { recursive: true });
}

await writeFile(resolve(dist, "index.html"), `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0; url=site/"><title>Agent Forge Public Showcase</title></head><body><p><a href="site/">Open the Agent Forge public showcase</a>.</p></body></html>\n`);
await writeFile(resolve(dist, ".nojekyll"), "");
console.log("Built GitHub Pages artifact in dist/");
