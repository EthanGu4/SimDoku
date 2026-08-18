import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const backendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "backend");
const isWindows = process.platform === "win32";
const venvPython = path.join(
  backendDir,
  ".venv",
  isWindows ? "Scripts" : "bin",
  isWindows ? "python.exe" : "python",
);
const pythonCmd = existsSync(venvPython) ? venvPython : "python";

const child = spawn(pythonCmd, ["-m", "uvicorn", "app.main:app", "--port", "8000", "--reload"], {
  cwd: backendDir,
  stdio: "inherit",
});

child.on("exit", (code) => process.exit(code ?? 0));
