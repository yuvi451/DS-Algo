# Deep dive: `src/agent/loop.ts`

**What it does in one line:** it sends the task to the model, runs whatever tools the model asks for, feeds the results back, and repeats until the model finishes, gets stuck, or runs out of turns.

The file has 5 parts:
1. Imports (L1–4)
2. Types that describe inputs, outputs and events (L6–36)
3. Three fixed messages (L38–52)
4. The `AgentLoop` class and its constructor (L54–69)
5. `run()`, the loop itself (L71–159)

---

## 1. Imports (L1–4)

```ts
import type { Message, ModelProvider, ModelTurn } from "../llm/provider.js";
import { ToolRegistry } from "../tools/registry.js";
import type { ToolResult } from "../tools/types.js";
import { buildSystemPrompt } from "./prompt.js";
```

> **TS basics**
> - `import type` brings in **types only**. They are removed when the code compiles, so nothing is loaded at runtime. `ToolRegistry` uses a normal `import` because the code calls `new ToolRegistry()`, so it has to exist at runtime.
> - The `.js` ending on a `.ts` file is normal in ESM/NodeNext projects. The path points to the compiled output.

What each import is for:

| Import | What it is |
|---|---|
| `Message` | One entry in the conversation. It is either a `user`, an `assistant` or a `tool` message. |
| `ModelProvider` | Anything that has `generateTurn(systemPrompt, history, tools) → Promise<ModelTurn>`. Gemini is one example. |
| `ModelTurn` | One reply from the model: `{ text, toolCalls, stopReason, errorMessage? }` |
| `ToolRegistry` | Holds all the tools. It gives you `.definitions` (what the model sees) and `.run(name, args, ctx)`. |
| `ToolResult` | `{ ok: boolean; output: string }` |
| `buildSystemPrompt` | Builds the system instructions string. |

---

## 2. Types (L6–36)

### `AgentStatus` (L10)
```ts
export type AgentStatus = "completed" | "unverified" | "blocked" | "max_turns_reached" | "error";
```
> **TS:** This is a **union of string literals**. The variable can only hold one of these exact strings, and TypeScript flags a typo like `"complete"`. `export` lets other files import it.

What each status means:
- `completed`: the model finished, and it either made no edits or its edits passed verification.
- `unverified`: the model edited files and was asked once to verify, but it stopped again without verifying.
- `blocked`: verification failed too many times, and the model was told to stop and report.
- `max_turns_reached`: the loop ran out of turns.
- `error`: the API call threw, or the model returned `stopReason: "error"`.

### `AgentRunResult` (L12–17)
```ts
export interface AgentRunResult { status; finalText; turnsUsed; history }
```
> **TS:** An `interface` describes the shape of an object. `Message[]` means "an array of `Message`".

This is what `run()` gives back to the caller: the status, the model's last text, how many turns it took, and the full conversation.

### `AgentEvent` (L19–26)
```ts
export type AgentEvent =
  | { type: "turn_start"; turn: number }
  | { type: "tool_call"; name: string; arguments: Record<string, unknown> }
  ...
```
> **TS:** This is a **discriminated union**. Every variant has a `type` field with a different literal value. Once you check `if (e.type === "tool_call")`, TypeScript knows `e.name` and `e.arguments` exist. This is called **narrowing**.
> - `Record<string, unknown>` means "an object with string keys and values of unknown type". `unknown` is the safe version of `any`: you have to check the value before you use it.

These events exist only to **report progress**. The loop emits them, and `index.ts` (`printEvent`) prints them. They never change what the loop does.

### `AgentLoopConfig` (L28–36)
```ts
maxTurns?: number;
onEvent?: (event: AgentEvent) => void;
```
> **TS:**
> - `?` makes a property **optional**, so its type is really `number | undefined`.
> - `(event: AgentEvent) => void` is a **function type**: it takes an event and returns nothing.
> - `/** ... */` is a JSDoc comment. Your editor shows it when you hover.

These are the constructor options. Only `provider` and `repoRoot` are required. Note that `maxVerifyRetries = 3` means **4 attempts in total**: the first try plus 3 retries.

---

## 3. Constants (L38–52)

| Constant | When it is used |
|---|---|
| `VERIFY_NUDGE` | The model tries to finish while it still has unverified edits. It gets sent back once with this message. |
| `STOP_MESSAGE` | Verification failed more times than `maxVerifyRetries`. The model is told to stop and write a report. |
| `CUT_OFF_RESULT` | The reply hit the output-token limit (`stopReason === "length"`). Its tool calls **are not run**, because the arguments may be cut off (for example, half a file). Each call gets this fake failure result instead. |

> **TS:** `const CUT_OFF_RESULT: ToolResult = {...}` is a **type annotation**. TypeScript checks that the object matches `ToolResult`. The `+` in the strings is ordinary string joining across lines.

---

## 4. Class and constructor (L54–69)

```ts
private readonly provider: ModelProvider;
...
this.maxTurns = config.maxTurns ?? 25;
this.emit = config.onEvent ?? (() => {});
```
> **TS:**
> - `private` means only code inside this class can use the field. This is checked at compile time.
> - `readonly` means the field can be set in the constructor and never changed after that.
> - `??` is **nullish coalescing**: use the right side only when the left side is `null` or `undefined`. This is different from `||`, which also replaces `0` and `""`. With `??`, `maxTurns: 0` would stay `0`.
> - `() => {}` is an empty arrow function that does nothing.

The defaults: 25 turns, 3 verify retries, a fresh `ToolRegistry`, and an `emit` that does nothing. Because `emit` always has a value, the rest of the code can call `this.emit(...)` without checking whether `onEvent` was passed.

---

## 5. `run(task)`: the loop (L71–155)

> **TS:** `async` functions always return a `Promise`. `Promise<AgentRunResult>` means the value will be an `AgentRunResult` once it resolves. Inside the function, `await` pauses until a promise settles.

### Setup (L72–79)
```ts
const history: Message[] = [{ role: "user", content: task }];
```
The conversation starts with the task as the first user message. After that, the loop keeps track of 5 things:

| Variable | Meaning |
|---|---|
| `failedVerifications` | How many verification runs **in a row** have failed. |
| `hasUnverifiedEdits` | The model wrote a file, and no verification has passed since. |
| `nudgedToVerify` | Whether `VERIFY_NUDGE` has already been sent (it is only sent once). |
| `mustStop` | The retry cap was hit, so the next reply ends the run. |
| `lastText` | The model's latest text, used as the fallback final answer. |

> **TS:** `const` means the variable can't be reassigned. `let` means it can. `history` is a `const`, but you can still `.push()` into it, because the array itself can be changed. Only the binding is fixed.

### Each turn (L81–151)

**Step A: call the model (L84–93)**
```ts
let reply: ModelTurn;
try {
  reply = await this.provider.generateTurn(systemPrompt, history, this.tools.definitions);
} catch (err) {
  return this.finish("error", `Model request failed: ${(err as Error).message}`, ...);
}
```
- The **full history is sent every turn**, because the model does not remember anything between calls.
- `reply` is declared before the `try` so it can still be used after the block.
- `err as Error` is a **type assertion**. In a `catch`, `err` has type `unknown`. This tells TypeScript to treat it as an `Error`. It is not checked at runtime.
- `` `...${x}` `` is a template string.
- If the call throws (network, auth), the run ends with `error`. If the model returns `stopReason === "error"`, the run also ends with `error`. `reply.errorMessage ?? "..."` supplies a fallback message.

**Step B: record the reply (L95–98)**
```ts
const { text, toolCalls, stopReason } = reply;
```
> **TS:** This is **object destructuring**. It pulls three fields into three variables. `if (text)` is a **truthiness** check, and an empty string `""` counts as false.

The assistant message is added to the history, including its tool calls. The text is emitted, and `lastText` is updated.

**Step C: stop if a stop was already asked for (L101–103)**
If `mustStop` was set on the previous turn, the model has now been sent `STOP_MESSAGE`. Whatever it replies with is its final report, so the run ends as `blocked`. This check comes **before** any tools run, so the model can't keep going.

**Step D: the model called no tools (L105–112).** It thinks it is done.
```
no unverified edits            → "completed"
unverified, already nudged     → "unverified"   (it ignored the nudge)
unverified, not yet nudged     → send VERIFY_NUDGE, go to the next turn
```
`continue` jumps straight to the next loop iteration.

**Step E: run each tool call (L114–147)**
> **TS:** `for (const call of toolCalls)` loops over the array **values**. (`for...in` would loop over the keys.) `cond ? a : b` is the ternary operator.

For every call:
1. Emit `tool_call`.
2. If the reply was cut off (`stopReason === "length"`), use `CUT_OFF_RESULT`. Otherwise, actually run the tool with `await this.tools.run(...)`.
3. Emit `tool_result`, then add a `role: "tool"` message to the history. `toolCallId` connects the result to the call it answers, which the APIs require. `isError: !result.ok` flips the boolean.
4. If the reply was cut off, `continue` here. The fake results do not count as edits or verifications.
5. A successful `write_file` sets `hasUnverifiedEdits = true`.
6. **Only a `bash` call with `verification: true` counts as verification** (L133). Anything else, such as `ls` or `grep`, skips the rest of this iteration. The check is `=== true` because the value is `unknown`, and only a real `true` should count, not `"true"` or `1`.
7. If the verification run succeeded, the fail counter goes back to 0 and the edits count as verified.
   If it failed, `failedVerifications` goes up by 1, and then:
   - if it is still at or below the cap, emit `verification_failed` (retry X of N)
   - if it is above the cap, emit `verification_cap_reached` once and set `mustStop = true`. The `!mustStop` guard stops this event from firing twice when one turn has several failing verifications.

**Step F: queue the stop message (L150)**
`STOP_MESSAGE` is added **after the loop over tool calls finishes**. The API expects every tool call to be followed by its result before any new user message. If the stop message went in the middle, it would break that order.

### Out of turns (L153–154)
The `for` loop ends without returning, so the run finishes as `max_turns_reached`. `lastText || fallback` uses the model's last text, or the fallback message if that text is empty.

### `finish()` (L157–159)
```ts
return { status, finalText, turnsUsed, history };
```
> **TS:** This is **shorthand property syntax**. `{ status }` is the same as `{ status: status }`.

It is a small private helper that builds the result object, so every exit point returns the same shape.

---

## The whole flow

```
history = [task]
repeat up to maxTurns:
    reply = model(history)            ── throws / error      → "error"
    save reply
    mustStop was set?                 ──                     → "blocked"
    no tool calls?
        no unverified edits           ──                     → "completed"
        already nudged                ──                     → "unverified"
        otherwise add VERIFY_NUDGE, next turn
    for each tool call:
        cut off? fake error : run the tool → save result
        write_file ok     → hasUnverifiedEdits = true
        verification ok   → reset the counter, edits count as verified
        verification fail → counter+1; above the cap → mustStop
    mustStop? add STOP_MESSAGE
out of turns                          ──                     → "max_turns_reached"
```

**Two details that are easy to miss:**
- `failedVerifications` counts failures **in a row**. One passing run sets it back to 0.
- `hasUnverifiedEdits` only tracks `write_file`. If the model changes files through `bash` (for example, `sed -i`), the loop doesn't know an edit happened.
