#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { AgentLoop, type AgentEvent } from "./agent/loop.js";
import { GeminiProvider } from "./llm/gemini.js";

const HELP = `Autonomous Coding Agent

Usage:
  aca --prompt "<task>" [--repo <path>] [--model <name>] [--max-turns <n>] [--max-verify-retries <n>]

Options:
  -p, --prompt <text>          The coding task, in plain English (required).
  -r, --repo <path>            The repository to work on. Default: current folder.
      --model <name>           Gemini model. Default: $GEMINI_MODEL or "gemini-2.0-flash".
      --max-turns <n>          Most turns the agent may take. Default: 25.
      --max-verify-retries <n> Retries after a failed verification run. Default: 3.
  -h, --help                   Show this help.

Environment (read from the shell, or from the .env file in the agent's folder):
  GEMINI_API_KEY   Required. Your Gemini API key.
  GEMINI_MODEL     Optional. Default model name.
`;

/** Loads the .env file next to package.json, if there is one. Variables already set in the shell win. */
function loadEnvFile(): void {
  try {
    process.loadEnvFile(new URL("../.env", import.meta.url));
  } catch {
    // No .env file: rely on the shell environment.
  }
}

interface CliArgs {
  prompt?: string;
  repo: string;
  model: string;
  maxTurns: number;
  maxVerifyRetries: number;
  help: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = {
    repo: process.cwd(),
    model: process.env.GEMINI_MODEL || "gemini-2.0-flash",
    maxTurns: 25,
    maxVerifyRetries: 3,
    help: false,
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case "-p":
      case "--prompt":
        args.prompt = argv[++i];
        break;
      case "-r":
      case "--repo":
        args.repo = path.resolve(argv[++i] ?? "");
        break;
      case "--model":
        args.model = argv[++i];
        break;
      case "--max-turns":
        args.maxTurns = Number(argv[++i]);
        break;
      case "--max-verify-retries":
        args.maxVerifyRetries = Number(argv[++i]);
        break;
      case "-h":
      case "--help":
        args.help = true;
        break;
      default:
        // A bare argument is treated as the prompt.
        if (!args.prompt && !arg.startsWith("-")) args.prompt = arg;
    }
  }
  return args;
}

/** Returns an error message, or undefined if the arguments are usable. */
function validate(args: CliArgs): string | undefined {
  if (!process.env.GEMINI_API_KEY) return "GEMINI_API_KEY is not set.";
  if (!fs.existsSync(args.repo) || !fs.statSync(args.repo).isDirectory()) return `Not a folder: ${args.repo}`;
  if (!Number.isInteger(args.maxTurns) || args.maxTurns < 1) return "--max-turns must be a whole number of 1 or more.";
  if (!Number.isInteger(args.maxVerifyRetries) || args.maxVerifyRetries < 0) {
    return "--max-verify-retries must be a whole number of 0 or more.";
  }
  return undefined;
}

function preview(text: string, maxChars: number): string {
  return text.length > maxChars ? `${text.slice(0, maxChars)}…` : text;
}

function printEvent(event: AgentEvent): void {
  switch (event.type) {
    case "turn_start":
      console.log(`\n── turn ${event.turn} ──`);
      break;
    case "assistant_text":
      console.log(`[model] ${event.text}`);
      break;
    case "tool_call":
      console.log(`  → ${event.name}(${preview(JSON.stringify(event.arguments), 160)})`);
      break;
    case "tool_result":
      console.log(`  ← [${event.ok ? "ok" : "FAILED"}] ${preview(event.output, 300).replace(/\n/g, "\n    ")}`);
      break;
    case "verification_failed":
      console.log(`  ! verification failed, retry ${event.retry} of ${event.maxRetries}`);
      break;
    case "verification_cap_reached":
      console.log(`  !! verification still failing after ${event.maxRetries} retries, asking for a final report`);
      break;
    case "verification_required":
      console.log("  ! model tried to finish without verifying its edits, asking it to verify");
      break;
  }
}

async function main(): Promise<void> {
  loadEnvFile();
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.prompt?.trim()) {
    console.log(HELP);
    process.exitCode = args.help ? 0 : 1;
    return;
  }

  const error = validate(args);
  if (error) {
    console.error(`Error: ${error}`);
    process.exitCode = 1;
    return;
  }

  const loop = new AgentLoop({
    provider: new GeminiProvider(process.env.GEMINI_API_KEY!, args.model, (message) => console.log(`  … ${message}`)),
    repoRoot: args.repo,
    maxTurns: args.maxTurns,
    maxVerifyRetries: args.maxVerifyRetries,
    onEvent: printEvent,
  });

  console.log(`Repo:   ${args.repo}`);
  console.log(`Model:  ${args.model}`);
  console.log(`Task:   ${args.prompt}`);

  const result = await loop.run(args.prompt);

  const rule = "=".repeat(60);
  console.log(`\n${rule}\nStatus:      ${result.status}\nTurns used:  ${result.turnsUsed}\n${rule}`);
  console.log(result.finalText);
  process.exitCode = result.status === "completed" ? 0 : 1;
}

main().catch((err) => {
  console.error("Fatal error:", err instanceof Error ? err.message : err);
  process.exitCode = 1;
});
