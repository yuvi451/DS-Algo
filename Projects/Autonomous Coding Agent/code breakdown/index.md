# Deep dive: `src/index.ts`

**What it does in one line:** it is the command-line entry point. It loads `.env`, reads the flags, checks them, connects `GeminiProvider` to `AgentLoop`, prints progress, and sets the exit code.

The file has 8 parts:
1. Shebang and imports (L1–5)
2. `HELP` text (L7–23)
3. `loadEnvFile` (L25–32)
4. `CliArgs` and `parseArgs` (L34–82)
5. `validate` (L84–93)
6. `preview` and `printEvent` (L95–123)
7. `main` (L125–159)
8. Starting `main` (L161–164)

---

## 1. Shebang and imports (L1–5)

```ts
#!/usr/bin/env node
import { AgentLoop, type AgentEvent } from "./agent/loop.js";
```
- `#!/usr/bin/env node` is a **shebang**. It lets the compiled `dist/index.js` run directly as a program. `package.json` exposes it as the `aca` command through `"bin"`.

> **TS basics:** `{ AgentLoop, type AgentEvent }` is an **inline type import**. One import line brings in a real value (`AgentLoop`) and a type only (`AgentEvent`).

---

## 2. `HELP` (L7–23)

This is a multi-line template string with the usage text. It is printed for `--help`, or when there's no prompt.

---

## 3. `loadEnvFile()` (L26–32)

```ts
try { process.loadEnvFile(new URL("../.env", import.meta.url)); } catch { /* no .env */ }
```
- `process.loadEnvFile` is built into Node (20.12+, which is why `package.json` sets `engines` to `>=20.12.0`). It reads `KEY=value` lines into `process.env`. Variables **already set in the shell win**, because they aren't overwritten.
- `import.meta.url` is the URL of **this compiled file** (`dist/index.js`). `new URL("../.env", that)` means "`.env` one folder up", which is the project root. So `.env` is found **no matter which folder you run `aca` from**.
- The `.env` file is optional, so a missing file is ignored silently.

> **TS:** `: void` as the return type means the function returns nothing.

---

## 4. `CliArgs` and `parseArgs(argv)` (L34–82)

```ts
interface CliArgs { prompt?: string; repo: string; model: string; maxTurns: number; maxVerifyRetries: number; help: boolean; }
```
`prompt` is optional, because the user might not have given one. `main` checks for that.

**Defaults (L44–50)**
| Field | Default |
|---|---|
| `repo` | `process.cwd()`, the folder you ran the command from |
| `model` | `$GEMINI_MODEL` or `"gemini-2.0-flash"` (`||` also replaces an empty string) |
| `maxTurns` | 25 |
| `maxVerifyRetries` | 3 |

**The parsing loop (L52–80)**
```ts
switch (arg) {
  case "-p":
  case "--prompt":
    args.prompt = argv[++i];
    break;
```
> **TS/JS:**
> - Two `case` labels with nothing between them **share** the same code. That's how `-p` and `--prompt` become aliases. (The `noFallthroughCasesInSwitch` setting allows empty cases like this.)
> - `argv[++i]` is **pre-increment**: it moves `i` forward first, then reads. That means "take the **next** argument as this flag's value, and skip over it".
> - `break` leaves the `switch`. Without it, the code would carry on into the next case.

| Flag | Effect |
|---|---|
| `-p`, `--prompt` | Sets the task |
| `-r`, `--repo` | `path.resolve(...)`, which makes the path absolute |
| `--model` | The model name |
| `--max-turns`, `--max-verify-retries` | `Number(...)`, which is `NaN` if the value isn't a number (`validate` catches that) |
| `-h`, `--help` | Show help |
| anything else | If there's no prompt yet and it doesn't start with `-`, **it becomes the prompt**. So `aca "fix the bug"` works |

Unknown flags like `--foo` are silently ignored.

---

## 5. `validate(args)` (L85–93)

```ts
function validate(args: CliArgs): string | undefined {
```
> **TS:** Returning `string | undefined` is a simple pattern: `undefined` means "no error", and a string is the error message.

Checks, in order:
1. `GEMINI_API_KEY` is set.
2. `repo` exists **and** is a folder (`fs.existsSync`, `fs.statSync`, synchronous calls that are fine at startup).
3. `maxTurns` is a whole number of at least 1. `Number.isInteger(NaN)` is `false`, so bad input fails here.
4. `maxVerifyRetries` is a whole number of at least 0. 0 is allowed and means "no retries".

---

## 6. `preview` and `printEvent` (L95–123)

```ts
function preview(text: string, maxChars: number): string {
  return text.length > maxChars ? `${text.slice(0, maxChars)}…` : text;
}
```
It cuts text for display and adds `…`. This only affects what is **printed**. The model still gets the full text.

```ts
function printEvent(event: AgentEvent): void {
  switch (event.type) {
    case "tool_call": console.log(`  → ${event.name}(${preview(JSON.stringify(event.arguments), 160)})`); ...
```
> **TS:** A `switch` on `event.type` narrows a **discriminated union**. Inside `case "tool_call"`, TypeScript knows `event.name` exists.

What gets printed:
```
── turn 3 ──
[model] Let me run the tests.
  → bash({"command":"npm test","verification":true})
  ← [FAILED] $ npm test
    (exit code: 1) ...                        ← .replace(/\n/g, "\n    ") indents the lines that follow
  ! verification failed, retry 1 of 3
  !! verification still failing after 3 retries, asking for a final report
  ! model tried to finish without verifying its edits, asking it to verify
```
The arguments are cut to 160 characters, and the results to 300.

---

## 7. `main()` (L125–159)

```ts
loadEnvFile();
const args = parseArgs(process.argv.slice(2));
```
`process.argv` is `[node path, script path, ...your args]`, so `.slice(2)` keeps only your arguments.

**Help or missing prompt (L128–132)**
```ts
if (args.help || !args.prompt?.trim()) { console.log(HELP); process.exitCode = args.help ? 0 : 1; return; }
```
A prompt of only spaces counts as missing. Asking for help exits with 0, and forgetting the prompt exits with 1.

> **Why `process.exitCode = 1` and not `process.exit(1)`:** setting the code lets Node finish writing output and then exit on its own. `process.exit()` stops immediately and can cut off printed text.

**Validation errors (L134–139)** are printed with `console.error`, which goes to stderr, and exit with 1.

**Connect everything (L141–147)**
```ts
const loop = new AgentLoop({
  provider: new GeminiProvider(process.env.GEMINI_API_KEY!, args.model, (message) => console.log(`  … ${message}`)),
  repoRoot: args.repo,
  maxTurns: args.maxTurns,
  maxVerifyRetries: args.maxVerifyRetries,
  onEvent: printEvent,
});
```
> **TS:** The `!` in `GEMINI_API_KEY!` is a **non-null assertion**. It tells TypeScript "this isn't `undefined`". That's safe here because `validate` already checked it. The check happens only at compile time, not at runtime.

This is the one place where the concrete parts meet: the Gemini provider, the retry printer, the event printer, and the settings.

**Run and report (L149–158)**
It prints the repo, model and task, then `await loop.run(prompt)`, then a summary box:
```
============================================================
Status:      completed
Turns used:  5
============================================================
<the model's final text>
```
The exit code is **0 only for `completed`**. Anything else (`unverified`, `blocked`, `error`, `max_turns_reached`) exits with 1, so scripts and CI can tell whether it worked.

---

## 8. Starting `main` (L161–164)

```ts
main().catch((err) => {
  console.error("Fatal error:", err instanceof Error ? err.message : err);
  process.exitCode = 1;
});
```
`main` is async, so it returns a Promise. `.catch` handles anything unexpected that escapes it. `instanceof Error` checks whether the value is a real Error object, because JavaScript lets you `throw` any value.

---

## Easy to miss
- `--model` as the **last** argument, with no value, sets `model` to `undefined`, even though the type says `string`. The request then goes to `models/undefined`. `--repo` with no value falls back to the current folder, because `path.resolve("")` returns the current directory.
- A second bare word, such as the "b" in `aca a b`, is ignored.
- The `GeminiProvider` constructor also throws when there's no key, but `validate` catches that case first with a clearer message.
