# Deep dive: `src/tools/bash.ts`

**What it does in one line:** it runs a shell command in the repo, with a timeout and a list of blocked destructive commands, and returns the exit code plus shortened stdout and stderr.

The file has 5 parts:
1. Imports and limits (L1–7)
2. `BLOCKED_COMMANDS` (L9–21)
3. `definition` (L24–48)
4. `execute` (L50–71)
5. `runCommand`, which starts the process (L74–105)

---

## 1. Imports and limits (L1–7)

```ts
import { spawn } from "node:child_process";
const DEFAULT_TIMEOUT_MS = 60_000;   // 1 minute
const MAX_TIMEOUT_MS = 300_000;      // 5 minutes
const MAX_OUTPUT_CHARS = 4000;
```
> **TS basics:** `import { spawn } from ...` is a **named import**. It takes one specific export out of the module. `spawn` starts a child process.

---

## 2. `BLOCKED_COMMANDS` (L10–21)

```ts
const BLOCKED_COMMANDS: RegExp[] = [ /\brm\s+(-\w*r\w*f\w*|-\w*f\w*r\w*)\s+(\/|~|\*|\.\.?\/?$)/i, ... ];
```
> **TS/regex:** `RegExp[]` is an array of regexes. In the patterns: `\b` is a word boundary, `\s+` is one or more spaces, `\w*` is any number of word characters, and `i` makes the match ignore case.

| Pattern | Blocks |
|---|---|
| `rm -rf` / `rm -fr` on `/`, `~`, `*`, `.`, `..` | Wiping the disk, the home folder, or the repo |
| `mkfs` | Formatting a disk |
| `dd if=... of=/dev/...` | Writing raw bytes to a device |
| `:(){ :\|:& };:` | A fork bomb (a process that copies itself until the machine hangs) |
| `curl ... \| sh` / `wget ... \| bash` | Running a downloaded script |
| `> /dev/sda` etc. | Writing to a raw disk |
| `shutdown`, `reboot` | Turning off the machine |
| `chmod -R 000 /` | Making the whole system unusable |
| `git push ... --force` | Rewriting the remote git history |

**This is a safety net, not a sandbox** (the comment says so). Commands that do the same thing in a different way get through, for example `rm -r -f /` (the flags are split) or `git push -f` (the short flag).

---

## 3. `definition` (L24–48)

| Arg | Meaning |
|---|---|
| `command` (required) | The shell command |
| `timeout_ms` | Timeout. Default 60s, maximum 300s |
| `verification` | `true` means "this command checks my edits" (tests, type-check, lint, build) |

`verification` is **the most important argument in the project**. The bash tool itself **ignores it completely**. Only `loop.ts` reads it (`call.arguments.verification === true`) to decide what counts as a verification pass or failure.

> **TS:** `` description: `Timeout ... Default ${DEFAULT_TIMEOUT_MS}` `` uses a template string, so the constants are inserted into the description. The text can't drift out of date with the code.

---

## 4. `execute(args, ctx)` (L50–71)

**a) Empty check (L51–52)**
`command.trim()` removes whitespace at both ends, so a command of only spaces is rejected too.

**b) Blocklist (L54–61)**
```ts
const blocked = BLOCKED_COMMANDS.find((pattern) => pattern.test(command));
```
> **TS:** `array.find(fn)` returns the **first** element for which `fn` returns true, or `undefined` if there is none.

If a pattern matches, it returns `ok: false` with the pattern that matched, and tells the model to ask the user to run the command instead.

**c) Timeout (L63–64)**
```ts
const requested = typeof args.timeout_ms === "number" ? args.timeout_ms : DEFAULT_TIMEOUT_MS;
const timeoutMs = Math.min(Math.max(requested, 1000), MAX_TIMEOUT_MS);
```
This is the **clamp** pattern: `Math.max` sets a floor of 1s, and `Math.min` sets a ceiling of 300s.

**d) Run it (L65)**
```ts
const { exitCode, stdout, stderr, timedOut } = await runCommand(command, ctx.repoRoot, timeoutMs);
```
The command runs **inside the repo folder** (`cwd`).

**e) Build the output (L67–70)**
```
$ npm test
(exit code: 1, killed after 60000ms)      ← the "killed" part only appears on timeout
--- stdout ---
...shortened to 4000 chars...
--- stderr ---
...shortened to 4000 chars...
```
- A section is only included if it isn't empty.
- `ok` is `exitCode === 0 && !timedOut`. Exit code 0 is the Unix way of saying "success".

---

## 5. `runCommand(command, cwd, timeoutMs)` (L74–105)

```ts
interface CommandResult { exitCode: number; stdout: string; stderr: string; timedOut: boolean; }
```
This interface isn't exported, so it is private to this file.

```ts
return new Promise((resolve) => {
  const child = spawn(command, { cwd, shell: true });
```
> **TS basics:**
> - `new Promise((resolve) => {...})` turns **event-based** code into a Promise that can be `await`ed. You call `resolve(value)` once, when you're done.
> - This Promise **never rejects**. Every outcome, including errors, is resolved as a `CommandResult`.
> - `{ cwd, shell: true }` uses shorthand: `cwd` means `cwd: cwd`.
> - `shell: true` runs the string through `/bin/sh`, so pipes, `&&` and globs work.

**Timeout (L88–91)**
```ts
const timer = setTimeout(() => { timedOut = true; child.kill("SIGKILL"); }, timeoutMs);
```
`setTimeout(fn, ms)` runs `fn` once after `ms` milliseconds. `SIGKILL` is a forced kill that the process can't ignore.

**Collect output (L94–95)**
```ts
child.stdout.setEncoding("utf8").on("data", (chunk: string) => (stdout += chunk));
```
- Output arrives in **chunks** through `"data"` events, and they're added to the string.
- `setEncoding("utf8")` handles multi-byte characters (like emoji) that get split across two chunks. Without it, you'd get broken characters.
- `(x) => (a += b)`: the brackets make it clear the arrow returns the assignment. That's fine, because the return value is ignored.

**Finish (L96–103)**
```ts
child.on("close", (code) => { clearTimeout(timer); resolve({ exitCode: timedOut ? -1 : (code ?? -1), ... }); });
child.on("error", (err) => { clearTimeout(timer); resolve({ exitCode: -1, ..., stderr: `${stderr}\n${err.message}` }); });
```
- `close` means the process ended and its output streams are closed. `code` is `null` when the process was killed by a signal, so `?? -1` covers that.
- `error` means the process couldn't be started (or couldn't be killed).
- `clearTimeout` cancels the timer, so it doesn't fire later on a process that has already finished.
- If both events fire, the second `resolve` is **ignored**, because a Promise only settles once.

---

## Easy to miss
- `kill` stops the **shell** process. Programs the shell started (for example a dev server) can survive a timeout.
- A command can still wait forever for input (for example `git commit` opening an editor) until the timeout kills it.
- Stdout and stderr are each shortened separately, so the combined output can be up to about 8000 characters plus the headers.
