export interface JsonSchema {
  type: string;
  description?: string;
  properties?: Record<string, JsonSchema>;
  items?: JsonSchema;
  required?: string[];
  enum?: string[];
}

/** What the model sees: the tool's name, what it does, and its arguments. */
export interface ToolDefinition {
  name: string;
  description: string;
  parameters: JsonSchema;
}

export interface ToolContext {
  /** Absolute path of the repository the agent works on. */
  repoRoot: string;
}

export interface ToolResult {
  ok: boolean;
  /** Text sent back to the model. */
  output: string;
}

export interface Tool {
  definition: ToolDefinition;
  execute(args: Record<string, unknown>, ctx: ToolContext): Promise<ToolResult>;
}
