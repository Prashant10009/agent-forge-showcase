import { access, readFile, readdir } from "node:fs/promises";
import { dirname, extname, relative, resolve, sep } from "node:path";

const root = resolve(import.meta.dirname, "..");
const skip = new Set([".git", "dist", "node_modules"]);
const candidates = [];
const missing = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (skip.has(entry.name)) continue;
    const absolute = resolve(directory, entry.name);
    if (entry.isDirectory()) await walk(absolute);
    else if ([".html", ".md"].includes(extname(entry.name).toLowerCase())) candidates.push(absolute);
  }
}

function localLinks(content, extension) {
  const values = [];
  const pattern = extension === ".md" ? /!?(?:\[[^\]]*\])\(([^)]+)\)/g : /(?:href|src)=["']([^"']+)["']/g;
  for (const match of content.matchAll(pattern)) values.push(match[1].trim().split(/[?#]/)[0]);
  return values.filter((value) => value && !/^(?:https?:|mailto:|#|data:|javascript:)/i.test(value));
}

await walk(root);

for (const file of candidates) {
  const content = await readFile(file, "utf8");
  for (const link of localLinks(content, extname(file).toLowerCase())) {
    const target = resolve(dirname(file), decodeURIComponent(link));
    try { await access(target); }
    catch { missing.push(`${relative(root, file).split(sep).join("/")} -> ${link}`); }
  }
}

if (missing.length) {
  console.error("Local link check failed:\n" + missing.map((item) => `- ${item}`).join("\n"));
  process.exit(1);
}
console.log(`Local link check passed across ${candidates.length} Markdown/HTML files.`);
