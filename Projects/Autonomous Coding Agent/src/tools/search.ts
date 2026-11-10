import fs from "node:fs/promises";
import path from "node:path";
import type { Tool } from "./types.js";
import { resolveInRepo } from "./util.js";

const SKIPPED_DIRS = new Set(["node_modules", "dist", "build", "out", "coverage", "__pycache__"]);
const MAX_MATCHES = 50;
const MAX_FILE_NAME_MATCHES = 20;
const MAX_FILES = 5000;
const MAX_FILE_BYTES = 1_000_000;

export const searchTool: Tool = {
  definition: {
    name: "codebase_search",
    description:
      "Search the repository's file names and file contents for a keyword or regex (case-insensitive). Use this " +
      "first to find the relevant files instead of guessing paths. Returns matching paths with line numbers.",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string", description: "Keyword or regular expression to search for." },
        path: { type: "string", description: "Optional folder (relative to the repo root) to search in." },
        regex: { type: "boolean", description: "Treat `query` as a regular expression. Default false." },
      },
      required: ["query"],
    },
  },

  async execute(args, ctx) {
    const query = String(args.query ?? "");
    if (!query) return { ok: false, output: "`query` must be a non-empty string." };
    const folder = typeof args.path === "string" && args.path ? args.path : ".";

    let startDir: string;
    let pattern: RegExp;
    try {
      startDir = resolveInRepo(ctx.repoRoot, folder);
      pattern = new RegExp(args.regex === true ? query : escapeRegExp(query), "i");
    } catch (err) {
      return { ok: false, output: (err as Error).message };
    }

    const nameMatches: string[] = [];
    const lineMatches: string[] = [];
    let filesSeen = 0;
    const isFull = () => lineMatches.length >= MAX_MATCHES || filesSeen >= MAX_FILES;

    async function walk(dir: string): Promise<void> {
      const entries = await fs.readdir(dir, { withFileTypes: true }).catch(() => []);
      for (const entry of entries) {
        if (isFull()) return;
        // Skips hidden entries such as .git, .env, and .venv.
        if (entry.name.startsWith(".")) continue;

        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (!SKIPPED_DIRS.has(entry.name)) await walk(fullPath);
          continue;
        }
        if (!entry.isFile()) continue;

        filesSeen++;
        const relPath = path.relative(ctx.repoRoot, fullPath);
        if (pattern.test(entry.name)) nameMatches.push(relPath);

        const lines = await readLines(fullPath);
        for (let i = 0; i < lines.length && lineMatches.length < MAX_MATCHES; i++) {
          if (pattern.test(lines[i])) lineMatches.push(`${relPath}:${i + 1}: ${lines[i].trim().slice(0, 200)}`);
        }
      }
    }

    await walk(startDir);

    if (nameMatches.length === 0 && lineMatches.length === 0) {
      return { ok: true, output: `No matches for "${query}" in "${folder}".` };
    }
    const sections: string[] = [];
    if (nameMatches.length > 0) {
      sections.push(`Matching file names:\n${nameMatches.slice(0, MAX_FILE_NAME_MATCHES).join("\n")}`);
    }
    if (lineMatches.length > 0) {
      const count = lineMatches.length >= MAX_MATCHES ? `${MAX_MATCHES}+, list cut short` : lineMatches.length;
      sections.push(`Matching lines (${count}):\n${lineMatches.join("\n")}`);
    }
    return { ok: true, output: sections.join("\n\n") };
  },
};

/** Returns no lines for files that are too big or can't be read, so one bad file doesn't stop the search. */
async function readLines(file: string): Promise<string[]> {
  try {
    if ((await fs.stat(file)).size > MAX_FILE_BYTES) return [];
    return (await fs.readFile(file, "utf-8")).split("\n");
  } catch {
    return [];
  }
}

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
