import { spawnSync } from "node:child_process";
import { delimiter, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const command = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const pythonPath = [resolve(root, "src"), process.env.PYTHONPATH].filter(Boolean).join(delimiter);
const result = spawnSync(
  command,
  ["-m", "unittest", "discover", "-s", "tests_python", "-v"],
  {
    cwd: root,
    env: { ...process.env, PYTHONPATH: pythonPath, PYTHONDONTWRITEBYTECODE: "1" },
    stdio: "inherit",
  },
);

if (result.error) {
  console.error(`Unable to start Python test runner: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
