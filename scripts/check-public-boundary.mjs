import { readFile, readdir, stat } from "node:fs/promises";
import { extname, relative, resolve, sep } from "node:path";

const root = resolve(import.meta.dirname, "..");
const skip = new Set([".git", "dist", "node_modules", "coverage"]);
const violations = [];

const forbiddenPathPatterns = [
  /(^|\/)(data|logs?|uploads?|chroma_db|builder_logs)(\/|$)/i,
  /(^|\/)(\.env(?!\.example$)|\.local_password)$/i,
  /\.(bak|db|docx|jsonl|pem|pfx|sqlite\d*|zip)$/i,
  /(^|\/)(sonnet|claude|codex)[_-]?handoff/i,
  /(^|\/)chat[_-]?audit/i
];

const forbiddenContentPatterns = [
  { name: "private production repository", pattern: /agent-forge-production/i },
  { name: "Windows user/workspace path", pattern: /[A-Z]:\\(?:Users|agent-forge)(?:\\|$)/i },
  { name: "MongoDB credential URI", pattern: /mongodb(?:\+srv)?:\/\/[^\s"']+:[^\s"']+@/i },
  { name: "private key block", pattern: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/ },
  { name: "OpenAI-style secret", pattern: /\bsk-[A-Za-z0-9_-]{20,}\b/ },
  { name: "GitHub token", pattern: /\bgh[pousr]_[A-Za-z0-9]{30,}\b/ },
  { name: "AWS access key", pattern: /\bAKIA[0-9A-Z]{16}\b/ },
  { name: "Google API key", pattern: /\bAIza[0-9A-Za-z_-]{30,}\b/ }
];

const allowedBinary = [
  /^assets\/screenshots\/[a-z0-9-]+\.png$/,
  /^assets\/social-preview\.png$/
];

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  for (const entry of entries) {
    if (skip.has(entry.name)) continue;
    const absolute = resolve(directory, entry.name);
    const repoPath = relative(root, absolute).split(sep).join("/");
    if (entry.isDirectory()) {
      await walk(absolute);
      continue;
    }
    if (!(await stat(absolute)).isFile()) continue;

    for (const pattern of forbiddenPathPatterns) {
      if (pattern.test(repoPath)) violations.push(`${repoPath}: forbidden path class`);
    }

    const extension = extname(repoPath).toLowerCase();
    if ([".png", ".gif", ".jpg", ".jpeg", ".webp", ".pdf"].includes(extension) && !allowedBinary.some((rule) => rule.test(repoPath))) {
      violations.push(`${repoPath}: binary asset is not allowlisted`);
      continue;
    }

    if (repoPath === "scripts/check-public-boundary.mjs" || [".png", ".gif", ".jpg", ".jpeg", ".webp", ".pdf"].includes(extension)) continue;
    const content = await readFile(absolute, "utf8");
    for (const { name, pattern } of forbiddenContentPatterns) {
      if (pattern.test(content)) violations.push(`${repoPath}: ${name}`);
    }
  }
}

await walk(root);

if (violations.length) {
  console.error("Public-boundary check failed:\n" + violations.map((item) => `- ${item}`).join("\n"));
  process.exit(1);
}

console.log("Public-boundary check passed: no forbidden paths, artifacts, or credential patterns found.");
