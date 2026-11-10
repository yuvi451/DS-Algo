import type { ToolDefinition } from "../tools/types.js";

/** The agent loop only speaks in these types. Each provider converts them to its own API format. */
export type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string; toolCalls?: ToolCall[] }
  | { role: "tool"; toolCallId: string; toolName: string; content: string; isError: boolean };

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  /** Provider data that must be sent back unchanged on later turns (e.g. Gemini's thought signature). */
  providerMetadata?: unknown;
}

export interface ModelTurn {
  text: string;
  /** Empty when the model thinks it is done. */
  toolCalls: ToolCall[];
  /**
   * Why the model stopped. "length": it hit the output limit, so the reply may be cut off.
   * "error": it failed to give a proper reply (e.g. a blocked prompt or a malformed tool call).
   */
  stopReason: "stop" | "length" | "error";
  errorMessage?: string;
}

export interface ModelProvider {
  generateTurn(systemPrompt: string, history: Message[], tools: ToolDefinition[]): Promise<ModelTurn>;
}
