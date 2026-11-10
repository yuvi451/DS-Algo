import { randomUUID } from "node:crypto";
import type { Message, ModelProvider, ModelTurn, ToolCall } from "./provider.js";
import type { JsonSchema, ToolDefinition } from "../tools/types.js";

const API_BASE = "https://generativelanguage.googleapis.com/v1beta/models";
const MAX_ATTEMPTS = 6;

interface GeminiPart {
  text?: string;
  functionCall?: { name: string; args?: Record<string, unknown> };
  functionResponse?: { name: string; response: { output: string } | { error: string } };
  /** Gemini thinking models require this to be sent back with their function calls. */
  thoughtSignature?: string;
}

interface GeminiContent {
  role: "user" | "model";
  parts: GeminiPart[];
}

interface GeminiResponse {
  candidates?: Array<{ content?: GeminiContent; finishReason?: string }>;
  promptFeedback?: { blockReason?: string };
}

/** Calls Gemini's REST API directly (no SDK), so the full request and response format is visible here. */
export class GeminiProvider implements ModelProvider {
  constructor(
    private readonly apiKey: string,
    private readonly model: string,
    /** Called before each retry wait, so a caller can show that the agent is waiting, not stuck. */
    private readonly onRetry: (message: string) => void = () => {},
  ) {
    if (!apiKey) throw new Error("GeminiProvider needs an API key (set GEMINI_API_KEY).");
  }

  async generateTurn(systemPrompt: string, history: Message[], tools: ToolDefinition[]): Promise<ModelTurn> {
    const body = JSON.stringify({
      systemInstruction: { parts: [{ text: systemPrompt }] },
      contents: toGeminiContents(history),
      tools: tools.length > 0 ? [{ functionDeclarations: tools.map(toFunctionDeclaration) }] : undefined,
    });

    for (let attempt = 1; ; attempt++) {
      const res = await fetch(`${API_BASE}/${this.model}:generateContent`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-goog-api-key": this.apiKey },
        body,
      });
      if (res.ok) return parseResponse((await res.json()) as GeminiResponse);

      const errorText = await res.text().catch(() => "");
      // Rate limits (429) and overload (503) are common on the free tier, so wait and retry those.
      // A used-up daily quota won't clear by waiting a few seconds, so that fails straight away.
      const dailyQuota = res.status === 429 && errorText.includes("PerDay");
      const retryable = (res.status === 429 || res.status === 503) && !dailyQuota;
      if (!retryable || attempt === MAX_ATTEMPTS) {
        const hint = dailyQuota ? " (daily quota used up; it resets at midnight Pacific time)" : "";
        throw new Error(`Gemini API request failed (${res.status} ${res.statusText})${hint}: ${errorText}`);
      }
      const delayMs = retryDelayMs(errorText, attempt);
      this.onRetry(`Gemini returned ${res.status}, retrying in ${Math.round(delayMs / 1000)}s (attempt ${attempt + 1} of ${MAX_ATTEMPTS})`);
      await sleep(delayMs);
    }
  }
}

/**
 * Gemini expects all tool results for one model turn in a single "user" content, so messages from the
 * same side are merged. It also rejects contents with no parts, so those are skipped.
 */
export function toGeminiContents(history: Message[]): GeminiContent[] {
  const contents: GeminiContent[] = [];

  const append = (role: GeminiContent["role"], parts: GeminiPart[]) => {
    if (parts.length === 0) return;
    const last = contents.at(-1);
    if (last?.role === role) last.parts.push(...parts);
    else contents.push({ role, parts });
  };

  for (const msg of history) {
    if (msg.role === "user") {
      append("user", [{ text: msg.content }]);
    } else if (msg.role === "tool") {
      const response = msg.isError ? { error: msg.content } : { output: msg.content };
      append("user", [{ functionResponse: { name: msg.toolName, response } }]);
    } else {
      const parts: GeminiPart[] = msg.content ? [{ text: msg.content }] : [];
      for (const call of msg.toolCalls ?? []) {
        const thoughtSignature = typeof call.providerMetadata === "string" ? call.providerMetadata : undefined;
        parts.push({ functionCall: { name: call.name, args: call.arguments }, thoughtSignature });
      }
      append("model", parts);
    }
  }

  return contents;
}

function parseResponse(data: GeminiResponse): ModelTurn {
  const candidate = data.candidates?.[0];
  if (!candidate) {
    const reason = data.promptFeedback?.blockReason ?? "no reply";
    return { text: "", toolCalls: [], stopReason: "error", errorMessage: `Gemini did not answer: ${reason}.` };
  }

  let text = "";
  const toolCalls: ToolCall[] = [];
  for (const part of candidate.content?.parts ?? []) {
    if (part.text) text += part.text;
    if (part.functionCall) {
      toolCalls.push({
        id: randomUUID(),
        name: part.functionCall.name,
        arguments: part.functionCall.args ?? {},
        providerMetadata: part.thoughtSignature,
      });
    }
  }

  // Same mapping as pi: STOP is a normal stop, MAX_TOKENS means cut off, anything else (SAFETY,
  // MALFORMED_FUNCTION_CALL, ...) is an error.
  const reason = candidate.finishReason ?? "STOP";
  if (reason === "STOP") return { text, toolCalls, stopReason: "stop" };
  if (reason === "MAX_TOKENS") return { text, toolCalls, stopReason: "length" };
  return { text, toolCalls, stopReason: "error", errorMessage: `Gemini stopped with finish reason ${reason}.` };
}

function toFunctionDeclaration(tool: ToolDefinition) {
  return { name: tool.name, description: tool.description, parameters: toGeminiSchema(tool.parameters) };
}

/** Gemini wants schema types in upper case (STRING, OBJECT, ...). */
function toGeminiSchema(schema: JsonSchema): Record<string, unknown> {
  const out: Record<string, unknown> = { type: schema.type.toUpperCase() };
  if (schema.description) out.description = schema.description;
  if (schema.enum) out.enum = schema.enum;
  if (schema.items) out.items = toGeminiSchema(schema.items);
  if (schema.required) out.required = schema.required;
  if (schema.properties) {
    out.properties = Object.fromEntries(
      Object.entries(schema.properties).map(([key, value]) => [key, toGeminiSchema(value)]),
    );
  }
  return out;
}

/** Uses the server's suggested wait (e.g. `"retryDelay": "37s"`) if given, else exponential backoff up to 30s. */
function retryDelayMs(errorText: string, attempt: number): number {
  const match = errorText.match(/"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"/);
  const seconds = match ? Number(match[1]) : Math.min(2 ** attempt, 30);
  return seconds * 1000 + Math.random() * 1000;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
