import type { JsonSchema, Tool, ToolContext, ToolDefinition, ToolResult } from "./types.js";
import { searchTool } from "./search.js";
import { readTool } from "./read.js";
import { writeTool } from "./write.js";
import { bashTool } from "./bash.js";

export class ToolRegistry {
  private readonly tools: Map<string, Tool>;

  constructor(tools: Tool[] = [searchTool, readTool, writeTool, bashTool]) {
    this.tools = new Map(tools.map((tool) => [tool.definition.name, tool]));
  }

  get definitions(): ToolDefinition[] {
    return [...this.tools.values()].map((tool) => tool.definition);
  }

  /** Never throws: errors become a failed result so the model can see them and react. */
  async run(name: string, args: Record<string, unknown>, ctx: ToolContext): Promise<ToolResult> {
    const tool = this.tools.get(name);
    if (!tool) {
      return { ok: false, output: `Unknown tool "${name}". Available tools: ${[...this.tools.keys()].join(", ")}` };
    }

    const problems = checkArgs(tool.definition.parameters, args);
    if (problems.length > 0) {
      return {
        ok: false,
        output: `Invalid arguments for "${name}":\n- ${problems.join("\n- ")}\nReceived: ${JSON.stringify(args)}`,
      };
    }

    try {
      return await tool.execute(args, ctx);
    } catch (err) {
      return { ok: false, output: `Tool "${name}" failed: ${(err as Error).message}` };
    }
  }
}

/** Like pi, checks arguments against the tool's schema before running it: required fields and basic types. */
function checkArgs(schema: JsonSchema, args: Record<string, unknown>): string[] {
  const problems: string[] = [];
  for (const key of schema.required ?? []) {
    if (args[key] == null) problems.push(`"${key}" is required`);
  }
  for (const [key, value] of Object.entries(args)) {
    const expected = schema.properties?.[key]?.type;
    const actual = Array.isArray(value) ? "array" : typeof value;
    if (expected && value != null && actual !== expected) problems.push(`"${key}" must be a ${expected}, got ${actual}`);
  }
  return problems;
}
