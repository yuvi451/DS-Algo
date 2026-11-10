import fs from "node:fs/promises";
import type { Tool } from "./types.js";
import { resolveInRepo, truncate } from "./util.js";

const MAX_CHARS = 8000;

export const readTool: Tool = {
  definition: {
    name: "read_file",
    description:
      "Read a file in the repository, given its path relative to the repo root. Returns the content with line " +
      "numbers. Long files are returned in parts: the output ends with the offset to use for the next part. " +
      "Reading a directory lists its entries.",
    parameters: {
      type: "object",
      properties: {
        path: { type: "string", description: "Path relative to the repo root, e.g. 'src/index.ts'." },
        offset: { type: "number", description: "Line number to start from (1 = first line). Default 1." },
        limit: { type: "number", description: "Most lines to return. Default: as many as fit." },
      },
      required: ["path"],
    },
  },

  async execute(args, ctx) {
    const relPath = String(args.path ?? "");
    if (!relPath) return { ok: false, output: "`path` must be a non-empty string." };

    try {
      const absPath = resolveInRepo(ctx.repoRoot, relPath);

      if ((await fs.stat(absPath)).isDirectory()) {
        const entries = await fs.readdir(absPath, { withFileTypes: true });
        const listing = entries.map((e) => `${e.isDirectory() ? "d" : "f"} ${e.name}`).sort().join("\n");
        return { ok: true, output: `"${relPath}" is a directory:\n${listing}` };
      }

      const lines = (await fs.readFile(absPath, "utf-8")).split("\n");
      const start = typeof args.offset === "number" ? Math.max(1, Math.floor(args.offset)) : 1;
      if (start > lines.length) {
        return { ok: false, output: `offset ${start} is past the end of "${relPath}" (${lines.length} lines).` };
      }
      const limit = typeof args.limit === "number" && args.limit >= 1 ? Math.floor(args.limit) : lines.length;
      const end = Math.min(lines.length, start + limit - 1);

      // Stop at whole lines once the output is full, so the model can ask for the rest with offset.
      let output = "";
      let last = start - 1;
      for (let n = start; n <= end; n++) {
        const line = `${n}\t${lines[n - 1]}\n`;
        if (output && output.length + line.length > MAX_CHARS) break;
        output += line;
        last = n;
      }
      // A single line longer than the budget still gets cut.
      output = truncate(output, MAX_CHARS);
      if (last < lines.length) {
        output += `\n[Showing lines ${start}-${last} of ${lines.length}. Use offset=${last + 1} to read more.]`;
      }
      return { ok: true, output };
    } catch (err) {
      const notFound = (err as NodeJS.ErrnoException).code === "ENOENT";
      return { ok: false, output: notFound ? `File not found: ${relPath}` : (err as Error).message };
    }
  },
};
