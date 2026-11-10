import fs from "node:fs/promises";
import path from "node:path";
import type { Tool } from "./types.js";
import { resolveInRepo } from "./util.js";

export const writeTool: Tool = {
  definition: {
    name: "write_file",
    description:
      "Create or overwrite a file in the repository, given its path relative to the repo root. This replaces the " +
      "whole file, so always pass the complete content, never a partial snippet. Missing folders are created.",
    parameters: {
      type: "object",
      properties: {
        path: { type: "string", description: "Path relative to the repo root, e.g. 'src/index.ts'." },
        content: { type: "string", description: "The complete file content." },
      },
      required: ["path", "content"],
    },
  },

  async execute(args, ctx) {
    const relPath = String(args.path ?? "");
    const content = typeof args.content === "string" ? args.content : "";
    if (!relPath) return { ok: false, output: "`path` must be a non-empty string." };

    try {
      const absPath = resolveInRepo(ctx.repoRoot, relPath);
      const existed = await fs.access(absPath).then(() => true, () => false);
      await fs.mkdir(path.dirname(absPath), { recursive: true });
      await fs.writeFile(absPath, content, "utf-8");

      const lines = content.split("\n").length;
      return { ok: true, output: `${existed ? "Overwrote" : "Created"} "${relPath}" (${lines} lines).` };
    } catch (err) {
      return { ok: false, output: `Could not write "${relPath}": ${(err as Error).message}` };
    }
  },
};
