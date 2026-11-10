# Deep dive: `src/agent.test.ts`

**What it does in one line:** it tests the real loop and the real tools, using a **scripted fake model** and a **fake Gemini server**, in temporary folders. It never touches the network.

How it runs: `npm test` does `tsc` first (compiling to `dist/`), then `node --test dist/agent.test.js`. It uses Node's built-in test runner, so no Jest or Vitest is needed.

The file has 3 parts:
1. Imports and the network guard (L1–14)
2. Helpers (L16–33)
3. 14 tests (L35–197)

---

## 1. Imports and network guard (L1–14)

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
```
> **TS basics**
> - `test(name, async fn)` registers one test. If `fn` throws or its Promise rejects, the test fails.
> - `assert/strict` means `assert.equal` uses `===` (strict equality), so `1` and `"1"` are different.

```ts
globalThis.fetch = async () => { throw new Error("Tests must not make network calls."); };
```
`globalThis` is the global object. Replacing `fetch` means any accidental real API call **fails loudly**. The Gemini tests put a fake `fetch` over this one, for one test at a time.

---

## 2. Helpers (L16–33)

```ts
const tempRepo = () => fs.mkdtemp(path.join(os.tmpdir(), "aca-"));
```
It creates a new empty temporary folder (like `/tmp/aca-x7Yq2`) to act as a repo, so tests never touch real files.

```ts
async function run(turns: ModelTurn[], repoRoot?: string) {
  const provider = { generateTurn: async () => turns.shift() ?? reply("out of turns") };
  return new AgentLoop({ provider, repoRoot: repoRoot ?? (await tempRepo()), maxVerifyRetries: 3 }).run("task");
}
```
> **TS:** `provider` is a plain object, not a class. It's accepted as a `ModelProvider` because its **shape** matches. This is **structural typing**. `turns.shift()` removes and returns the first element, or `undefined` when the array is empty.

This is **the key trick**: the "model" just hands back pre-written replies in order. The **real** loop and the **real** tools run on them, so you can test the loop's decisions exactly.

```ts
const reply = (text) => ({ text, toolCalls: [], stopReason: "stop" });   // model says it's done
const call = (name, args) => ({ text: "", toolCalls: [{ id: String(++callId), name, arguments: args }], stopReason: "stop" });
const edit = () => call("write_file", { path: "a.txt", content: "hi" });
const verify = (command) => call("bash", { command, verification: true });
const done = reply("done");
```
- `callId` is a counter, so every call gets a unique id.
- `verify("true")` and `verify("false")` use the shell commands `true` (always exits 0) and `false` (always exits 1). That's an easy way to make a verification pass or fail.
- `edit` and `verify` are **functions**, so each use creates a new call with a new id. `done` is a single shared value, because it has no id.

---

## 3. The tests

### Loop status logic (L35–86)

| # | Script (one item per turn) | Expected | What it proves |
|---|---|---|---|
| 1 | `done` | `completed` | No edits means done straight away |
| 2 | `edit, verify✓, done` | `completed` | The normal happy path |
| 3 | `edit, done, done` | `unverified`, 3 turns | The first `done` gets `VERIFY_NUDGE`. Ignoring it gives `unverified` |
| 4 | `edit, done, verify✓, done` | `completed` | Obeying the nudge works |
| 5 | `edit, verify✗, done, done` | `unverified` | A failed verification doesn't count as verified |
| 6a | `edit, inspect✗, verify✗ ×4, done` | `blocked`, 7 turns | The 4th failure goes past the 3 retries, so `STOP_MESSAGE` is sent and the next reply ends the run. `inspect` (bash **without** `verification`) failing is **not** counted |
| 6b | `edit, verify✗ ×3, verify✓, done` | `completed` | A pass within the retries recovers the run |
| 7 | a turn with `stopReason: "error"` / a provider that throws `"503"` | `error` | Both error paths, and the message is kept in `finalText` |
| 8 | `edit` with `stopReason: "length"`, then `done` | `completed` | The cut-off call was **not run** (`a.txt` doesn't exist), and history holds the "output limit" error |

> **TS in test 8:** `{ ...edit(), stopReason: "length" }` uses **object spread** to copy every field and then override one. `assert.rejects(promise)` passes if the promise **rejects**. Here that shows the file doesn't exist.

> **TS in test 7:** `async (): Promise<ModelTurn> => { throw ... }` gives an explicit return type. Without it, TypeScript would infer `Promise<never>`, because the function only throws.

### Tools (L88–124)

**Test 9: the safety checks** call `ToolRegistry` directly, without the loop:
- a missing `content` gives `"content" is required` (registry `checkArgs`)
- `path: 5` gives `"path" must be a string` (registry `checkArgs`)
- `read_file ../x`, `write_file /tmp/x`, and `codebase_search path ../..` are all refused (`resolveInRepo`)
- `bash rm -rf /` is refused (the blocklist)

**Test 10: search** writes `hello.ts` containing `greeting`, then checks that the output has `hello.ts:1:`.

**Test 11: reading in parts**
```ts
const lines = Array.from({ length: 500 }, (_, i) => `line ${i + 1} ${"x".repeat(40)}`);
```
> **TS:** `Array.from({ length: n }, fn)` builds an array of n items using `fn(value, index)`. `_` is the usual name for a parameter you don't use.

The 500 lines of about 50 characters are larger than 8000 characters. The test checks that:
- the first read gives an `offset=N` footer, with no `cut` (it ended on a whole line)
- reading from `offset=N` starts exactly at line N
- `offset 10, limit 2` gives exactly lines 10–11 plus a footer
- `offset 900` (past the end) gives `ok: false`

`?.[1]` in `match(...)?.[1]` protects against `match` returning `null`.

### Gemini client (L126–157)

**Test 12: retries and daily quota**
```ts
const fetchMock = t.mock.method(globalThis, "fetch", async () => responses.shift());
```
> **TS:** `t.mock.method(obj, "name", fake)` swaps a method for this test only, then **puts the original back automatically**. It also counts calls (`fetchMock.mock.callCount()`).

The fake responses, in order: `503 (retryDelay 0s)`, then `200 "hi"`, then `429 PerDay`.
- The first `generateTurn` gets 503, retries, gets "hi", and the `onRetry` message matches `attempt 2 of 6`.
- The second gets 429 PerDay and **throws immediately** with "daily quota".
- `fetch` was called exactly 3 times, which proves the daily quota was **not** retried.

`Response` is the built-in class for HTTP responses, so a fake one is easy to make.

**Test 13: converting history.** It hand-builds a history (task, assistant with 2 calls, 2 tool results where one is an error, a nudge, an empty assistant) and checks:
- the Gemini contents are `[user 1 part] [model 2 parts] [user 3 parts]`. The two results and the nudge are merged, and the empty assistant is dropped
- a good result is sent as `{ output }` and an error as `{ error }`

### Full run (L159–197)

**Test 14: a real bug fix, end to end, against a fake Gemini API**

The setup has a broken `math.js` (`a - b`) and a `test.js` that exits with 1 unless `add(2,3) === 5`.

The script the fake Gemini replies with:
1. `codebase_search "add"`
2. `read_file math.js` **and** `bash node test.js` (verification, which **fails**), both in one turn
3. `write_file math.js` with `a + b`
4. `bash node test.js` (verification, which **passes**)
5. the text "Fixed add()."

On **every** request, the fake `fetch` also checks what the client sent:
- the key is in the `x-goog-api-key` header and **not** in the URL
- no content is empty, and roles alternate (never two `user` contents in a row)
- every `functionCall` carries `thoughtSignature: "sig"`, and the next content has exactly as many `functionResponse`s as there were calls

> **TS:** `ReturnType<typeof toGeminiContents>` means "whatever type `toGeminiContents` returns". It lets the test use a type that isn't exported. `init.body as string` is a cast, because `RequestInit.body` has a wide type.

At the end, the status is `completed`, 5 turns were used, and `math.js` on disk now contains `a + b`.

This is the most valuable test. It runs the CLI's real path (the `GeminiProvider` → `AgentLoop` → tools → file system) with only the network faked.

---

## What isn't tested
`index.ts` (argument parsing and printing), bash timeouts, and search limits have no tests.
