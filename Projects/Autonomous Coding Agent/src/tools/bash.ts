import { spawn } from "node:child_process";
import type { Tool } from "./types.js";
import { truncate } from "./util.js";

const DEFAULT_TIMEOUT_MS = 60_000;
const MAX_TIMEOUT_MS = 300_000;
const MAX_OUTPUT_CHARS = 4000;

/** Blocks obviously destructive commands. This is a safety net, not a sandbox. */
const BLOCKED_COMMANDS: RegExp[] = [
  /\brm\s+(-\w*r\w*f\w*|-\w*f\w*r\w*)\s+(\/|~|\*|\.\.?\/?$)/i, // rm -rf on /, ~, *, . or ..
  /\bmkfs\b/i,
  /\bdd\s+if=.*of=\/dev\//i,
  /:\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:/, // fork bomb
  /\b(curl|wget)\b[^\n]*\|\s*(sh|bash|zsh|sudo)\b/i, // piping a download into a shell
  />\s*\/dev\/(sd|nvme|hd)[a-z]/i, // writing to a raw disk
  /\bshutdown\b/i,
  /\breboot\b/i,
  /\bchmod\s+-R\s+000\s+\//i,
  /\bgit\s+push\s+.*--force/i,
];

export const bashTool: Tool = {
  definition: {
    name: "bash",
    description:
      "Run a shell command in the repo root and get back the exit code and output. Use it to run the project's " +
      "tests, type-checker, linter, or build after an edit, or to look around (e.g. `cat package.json`). Work " +
      "out the right verification command for this project yourself. Long output is cut short, and obviously " +
      "destructive commands are blocked.",
    parameters: {
      type: "object",
      properties: {
        command: { type: "string", description: "The shell command to run." },
        timeout_ms: {
          type: "number",
          description: `Timeout in milliseconds. Default ${DEFAULT_TIMEOUT_MS}, max ${MAX_TIMEOUT_MS}.`,
        },
        verification: {
          type: "boolean",
          description:
            "Set to true when this command checks your edits (tests, type-check, lint, build). Only these runs " +
            "count toward finishing the task and toward the retry limit. Leave it unset for commands like ls or cat.",
        },
      },
      required: ["command"],
    },
  },

  async execute(args, ctx) {
    const command = String(args.command ?? "");
    if (!command.trim()) return { ok: false, output: "`command` must be a non-empty string." };

    const blocked = BLOCKED_COMMANDS.find((pattern) => pattern.test(command));
    if (blocked) {
      return {
        ok: false,
        output: `Blocked: this command matches ${blocked}, which is on the list of destructive commands. ` +
          "If it is really needed, ask the user to run it.",
      };
    }

    const requested = typeof args.timeout_ms === "number" ? args.timeout_ms : DEFAULT_TIMEOUT_MS;
    const timeoutMs = Math.min(Math.max(requested, 1000), MAX_TIMEOUT_MS);
    const { exitCode, stdout, stderr, timedOut } = await runCommand(command, ctx.repoRoot, timeoutMs);

    let output = `$ ${command}\n(exit code: ${exitCode}${timedOut ? `, killed after ${timeoutMs}ms` : ""})\n`;
    if (stdout.trim()) output += `--- stdout ---\n${truncate(stdout, MAX_OUTPUT_CHARS)}\n`;
    if (stderr.trim()) output += `--- stderr ---\n${truncate(stderr, MAX_OUTPUT_CHARS)}\n`;
    return { ok: exitCode === 0 && !timedOut, output };
  },
};

interface CommandResult {
  exitCode: number;
  stdout: string;
  stderr: string;
  timedOut: boolean;
}

function runCommand(command: string, cwd: string, timeoutMs: number): Promise<CommandResult> {
  return new Promise((resolve) => {
    const child = spawn(command, { cwd, shell: true });
    let stdout = "";
    let stderr = "";
    let timedOut = false;

    const timer = setTimeout(() => {
      timedOut = true;
      child.kill("SIGKILL");
    }, timeoutMs);

    // setEncoding keeps multi-byte characters intact when they are split across chunks.
    child.stdout.setEncoding("utf8").on("data", (chunk: string) => (stdout += chunk));
    child.stderr.setEncoding("utf8").on("data", (chunk: string) => (stderr += chunk));
    child.on("close", (code) => {
      clearTimeout(timer);
      resolve({ exitCode: timedOut ? -1 : (code ?? -1), stdout, stderr, timedOut });
    });
    child.on("error", (err) => {
      clearTimeout(timer);
      resolve({ exitCode: -1, stdout, stderr: `${stderr}\n${err.message}`, timedOut: false });
    });
  });
}
