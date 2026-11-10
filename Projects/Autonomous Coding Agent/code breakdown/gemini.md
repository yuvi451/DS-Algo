# Deep dive: `src/llm/gemini.ts`

**What it does in one line:** it converts the common `Message[]` history into Gemini's REST format, sends it with `fetch` (retrying on rate limits), and converts Gemini's answer back into a `ModelTurn`.

It uses **no SDK**, just a plain HTTP request, so the whole request and response format is visible in this file.

The file has 8 parts:
1. Imports and constants (L1–6)
2. Gemini's own types (L8–24)
3. `GeminiProvider` class: constructor and `generateTurn` with retries (L26–66)
4. `toGeminiContents`, which converts history to Gemini's format (L68–99)
5. `parseResponse`, which converts Gemini's answer to a `ModelTurn` (L101–128)
6. `toFunctionDeclaration` and `toGeminiSchema`, which convert the tools (L130–147)
7. `retryDelayMs` (L149–154)
8. `sleep` (L156–158)

---

## 1. Imports and constants (L1–6)

```ts
import { randomUUID } from "node:crypto";
const API_BASE = "https://generativelanguage.googleapis.com/v1beta/models";
const MAX_ATTEMPTS = 6;
```
`randomUUID()` makes a unique id string. Gemini doesn't give tool calls ids, so this file creates them. `MAX_ATTEMPTS` is 1 try plus 5 retries.

---

## 2. Gemini's types (L8–24)

```ts
interface GeminiPart {
  text?: string;
  functionCall?: { name: string; args?: Record<string, unknown> };
  functionResponse?: { name: string; response: { output: string } | { error: string } };
  thoughtSignature?: string;
}
interface GeminiContent { role: "user" | "model"; parts: GeminiPart[]; }
interface GeminiResponse {
  candidates?: Array<{ content?: GeminiContent; finishReason?: string }>;
  promptFeedback?: { blockReason?: string };
}
```
> **TS basics:**
> - `{ output: string } | { error: string }` is a union: the value is one shape or the other.
> - `Array<T>` is the same as `T[]`.
> - These interfaces aren't exported, so they are private to this file. Nothing else needs to know Gemini's format.

How Gemini's format differs from ours:

| Ours (`Message`) | Gemini |
|---|---|
| 3 roles: `user`, `assistant`, `tool` | 2 roles: `user`, `model` |
| One message = one piece of content | One content = a list of **parts** (text, function call, or function response) |
| Tool results are `role: "tool"` | Tool results are `functionResponse` parts inside a **`user`** content |

---

## 3. `GeminiProvider` (L27–66)

### Constructor (L28–35)
```ts
export class GeminiProvider implements ModelProvider {
  constructor(
    private readonly apiKey: string,
    private readonly model: string,
    private readonly onRetry: (message: string) => void = () => {},
  ) {
    if (!apiKey) throw new Error("GeminiProvider needs an API key (set GEMINI_API_KEY).");
  }
```
> **TS:**
> - `implements ModelProvider` asks TypeScript to check that this class really has a matching `generateTurn`.
> - `private readonly apiKey: string` **in the constructor's parameter list** is a **parameter property**. It declares the field and assigns it in one step. It's shorthand for writing `private readonly apiKey: string;` plus `this.apiKey = apiKey;`.
> - `= () => {}` gives `onRetry` a default that does nothing.

It fails early if there is no key. `onRetry` lets the CLI print "retrying in 5s…" so a slow run doesn't look frozen.

### `generateTurn` (L37–65)

**a) Build the request body once (L38–42)**
```ts
const body = JSON.stringify({
  systemInstruction: { parts: [{ text: systemPrompt }] },
  contents: toGeminiContents(history),
  tools: tools.length > 0 ? [{ functionDeclarations: tools.map(toFunctionDeclaration) }] : undefined,
});
```
`JSON.stringify` **leaves out** keys whose value is `undefined`, so an empty tool list simply isn't sent. The body is built **outside** the retry loop and reused for every attempt.

**b) The retry loop (L44)**
```ts
for (let attempt = 1; ; attempt++) {
```
> **TS/JS:** A `for` loop with no condition runs forever. The only ways out are `return` (success) and `throw` (give up).

**c) Send the request (L45–50)**
```ts
const res = await fetch(`${API_BASE}/${this.model}:generateContent`, {
  method: "POST",
  headers: { "Content-Type": "application/json", "x-goog-api-key": this.apiKey },
  body,
});
if (res.ok) return parseResponse((await res.json()) as GeminiResponse);
```
- `fetch` is built into Node 18+, so no library is needed.
- The API key goes in a **header**, not in the URL. URLs end up in logs, and the tests check this.
- `res.ok` is true for any 2xx status code.
- `as GeminiResponse` is a **cast** and is not checked at runtime. That's why `parseResponse` uses `?.` everywhere.

**d) Decide whether to retry (L52–60)**
```ts
const errorText = await res.text().catch(() => "");
const dailyQuota = res.status === 429 && errorText.includes("PerDay");
const retryable = (res.status === 429 || res.status === 503) && !dailyQuota;
if (!retryable || attempt === MAX_ATTEMPTS) throw new Error(`Gemini API request failed (...)${hint}: ${errorText}`);
```
| Status | What happens |
|---|---|
| 429 rate limit (per minute) | Wait, then retry |
| 503 overloaded | Wait, then retry |
| 429 with `PerDay` in the body | The daily quota is used up, so waiting won't help: throw now, with a hint |
| Anything else (400, 401, 404…) | Throw now |
| Retryable but this was attempt 6 | Throw |

The error thrown here is caught in `loop.ts`, which ends the run with status `error`.

**e) Wait, then loop again (L61–63)**
```ts
const delayMs = retryDelayMs(errorText, attempt);
this.onRetry(`Gemini returned ${res.status}, retrying in ${Math.round(delayMs / 1000)}s (attempt ${attempt + 1} of ${MAX_ATTEMPTS})`);
await sleep(delayMs);
```

---

## 4. `toGeminiContents(history)` (L72–99)

This is exported so the tests can check it directly.

```ts
const append = (role: GeminiContent["role"], parts: GeminiPart[]) => {
  if (parts.length === 0) return;
  const last = contents.at(-1);
  if (last?.role === role) last.parts.push(...parts);
  else contents.push({ role, parts });
};
```
> **TS:**
> - `GeminiContent["role"]` is an **indexed access type**. It means "the type of the `role` field", which is `"user" | "model"`. If that type changes, this code follows automatically.
> - `array.at(-1)` gives the last element, or `undefined` if the array is empty.
> - `last?.role` is optional chaining, which is safe when `last` is `undefined`.
> - `push(...parts)` **spreads** the array, so each part is pushed separately.

`append` enforces two Gemini rules:
1. **No empty contents.** Content with no parts is skipped (for example an assistant reply with no text and no calls).
2. **Consecutive items with the same role are merged.** Gemini wants the roles to alternate, and all tool results for one model turn in **one** `user` content.

Converting each message:

| Our message | Becomes |
|---|---|
| `user` | `user` part `{ text }` |
| `tool` | `user` part `{ functionResponse: { name, response: { output } or { error } } }` |
| `assistant` | `model` parts: the text (if any), plus one `{ functionCall, thoughtSignature }` per tool call |

```ts
const thoughtSignature = typeof call.providerMetadata === "string" ? call.providerMetadata : undefined;
```
This takes the signature saved from Gemini's earlier reply and sends it back. It's the other half of what `parseResponse` stores.

Example: `[user task] [assistant: 2 calls] [tool] [tool] [user nudge]` becomes `user(1 part)`, `model(2 parts)`, `user(3 parts)`. The two tool results **and** the nudge are merged into one user content.

---

## 5. `parseResponse(data)` (L101–128)

**a) No answer (L102–106)**
```ts
const candidate = data.candidates?.[0];
if (!candidate) return { text: "", toolCalls: [], stopReason: "error", errorMessage: `Gemini did not answer: ${reason}.` };
```
Gemini returns no candidates when the **prompt** was blocked. `promptFeedback.blockReason` says why.

**b) Collect text and tool calls (L108–120)**
For each part:
- text is added to `text`
- a `functionCall` becomes a `ToolCall` with a fresh `randomUUID()` id, `args ?? {}`, and the `thoughtSignature` stored in `providerMetadata`

**c) Map the finish reason (L124–127)**
| Gemini `finishReason` | `stopReason` |
|---|---|
| `STOP` (or missing) | `"stop"` |
| `MAX_TOKENS` | `"length"` |
| anything else (`SAFETY`, `MALFORMED_FUNCTION_CALL`, …) | `"error"`, with a message |

---

## 6. Converting the tools (L130–147)

```ts
function toFunctionDeclaration(tool: ToolDefinition) {
  return { name: tool.name, description: tool.description, parameters: toGeminiSchema(tool.parameters) };
}
```
> **TS:** It has no return type annotation, so TypeScript **infers** one from the returned object.

```ts
function toGeminiSchema(schema: JsonSchema): Record<string, unknown> {
  const out: Record<string, unknown> = { type: schema.type.toUpperCase() };
  ...
  if (schema.items) out.items = toGeminiSchema(schema.items);
  if (schema.properties) out.properties = Object.fromEntries(
    Object.entries(schema.properties).map(([key, value]) => [key, toGeminiSchema(value)]),
  );
```
> **TS:** `Object.entries` turns an object into `[key, value]` pairs. `.map` changes each value. `Object.fromEntries` turns the pairs back into an object. This is the standard way to "map over an object's values".

Gemini wants the types in **upper case** (`"string"` becomes `"STRING"`). The function copies only the fields that are present, and calls itself for nested `items` and `properties` (**recursion**).

---

## 7. `retryDelayMs(errorText, attempt)` (L150–154)

```ts
const match = errorText.match(/"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"/);
const seconds = match ? Number(match[1]) : Math.min(2 ** attempt, 30);
return seconds * 1000 + Math.random() * 1000;
```
> **TS/regex:** `string.match(regex)` returns `null`, or an array where `[1]` is the first **capture group** `( )`. `(?: )` is a group that is **not** captured. `2 ** n` means 2 to the power n.

- If Gemini's error body suggests a wait (`"retryDelay": "37s"`), it uses that.
- Otherwise it uses **exponential backoff**: 2, 4, 8, 16, 30, 30 seconds.
- It adds up to 1s of random **jitter**, so that many clients don't all retry at the same moment.

---

## 8. `sleep(ms)` (L156–158)

```ts
return new Promise((resolve) => setTimeout(resolve, ms));
```
This turns `setTimeout` into something you can `await`. It resolves after `ms` milliseconds.

---

## Easy to miss
- **`toolCallId` is never sent to Gemini.** Gemini matches results to calls by **name and order**, so the ids here only matter inside our own `history`.
- A new UUID is created for each call on each parse. Ids don't carry across turns, and nothing needs them to.
- The API key is sent only in the header, and the tests check that it never appears in the URL.
