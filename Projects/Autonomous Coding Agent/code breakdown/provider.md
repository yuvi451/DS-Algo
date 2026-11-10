# Deep dive: `src/llm/provider.ts`

**What it does in one line:** it defines the model-independent types the loop uses (messages, tool calls, one model reply), and the single method every model provider has to implement.

This file only has types. Its point is to keep the loop **independent of any one vendor**: `loop.ts` never mentions Gemini. To add Claude or OpenAI, you'd write another class that implements `ModelProvider`, and the loop stays the same.

The file has 4 parts:
1. `Message` (L3–7)
2. `ToolCall` (L9–15)
3. `ModelTurn` (L17–27)
4. `ModelProvider` (L29–31)

---

## 1. `Message` (L4–7)

```ts
export type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string; toolCalls?: ToolCall[] }
  | { role: "tool"; toolCallId: string; toolName: string; content: string; isError: boolean };
```
> **TS basics:** This is a **discriminated union** where `role` tells the variants apart. After `if (msg.role === "tool")`, TypeScript lets you use `msg.toolCallId`. In the other branches it doesn't. `gemini.ts` relies on exactly this.

| Role | Who adds it | Contains |
|---|---|---|
| `user` | The task, `VERIFY_NUDGE`, `STOP_MESSAGE` | Text |
| `assistant` | The model's reply | Text, plus the tool calls it asked for (if any) |
| `tool` | The loop, after running a tool | The result, which call it answers (`toolCallId`), and whether it failed |

The `history: Message[]` in the loop is simply a list of these, in order.

---

## 2. `ToolCall` (L9–15)

```ts
export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  providerMetadata?: unknown;
}
```
- `id` connects a call to its result (`toolCallId` in the `tool` message).
- `name` and `arguments` say which tool the model wants, and with what arguments.
- `providerMetadata` is opaque data the provider needs **sent back unchanged** on later turns. Gemini "thinking" models attach a `thoughtSignature` to function calls and reject the conversation if it's missing. The loop never looks at it. It just keeps it inside `history`.

> **TS:** `unknown` is the right type for "someone else's data that we only pass along". Nobody can use it by accident without checking it first.

---

## 3. `ModelTurn` (L17–27)

```ts
export interface ModelTurn {
  text: string;
  toolCalls: ToolCall[];
  stopReason: "stop" | "length" | "error";
  errorMessage?: string;
}
```
This is one reply from the model, already converted to the common format.
- `toolCalls` is **empty** when the model thinks it's done. That is how the loop recognises "finished".
- `stopReason`:
  - `"stop"`: a normal end.
  - `"length"`: it hit the output-token limit, so the reply may be cut off. The loop doesn't run its tool calls.
  - `"error"`: a blocked prompt, a malformed tool call, and so on. The loop ends with `error`.
- `errorMessage` is optional, and filled in when `stopReason` is `"error"`.

---

## 4. `ModelProvider` (L29–31)

```ts
export interface ModelProvider {
  generateTurn(systemPrompt: string, history: Message[], tools: ToolDefinition[]): Promise<ModelTurn>;
}
```
> **TS:** An interface with one method is a **contract**. A class can declare `implements ModelProvider` (as `GeminiProvider` does), but that's optional. TypeScript uses **structural typing**, so any object with a matching `generateTurn` counts. The tests use exactly that: `{ generateTurn: async () => ... }` is a valid provider without any class.

The contract: given the system prompt, the full history, and the tool list, return the model's next reply.
