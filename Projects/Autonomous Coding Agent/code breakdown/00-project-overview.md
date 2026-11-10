# Autonomous Coding Agent: full project breakdown and system design (interview prep)

Read this first. The other files in this folder go line by line through each source file. This one explains
**the whole system**: what each part does, why it was built that way, what it gives up, and how you'd
explain it in an interview.

---

## 1. The pitch

**30 seconds:**
> It's a small coding agent in TypeScript. You give it a task in plain English and a repo. It searches the
> code, reads the files it needs, edits them, runs the project's own tests to check its work, and fixes
> its mistakes until the tests pass. The key idea is that **"done" is checked by code, not trusted from the
> model**. If the model edited files, the run can only end as `completed` after a test run passes following
> the last edit.

**2 minutes (add these points):**
- It's a **loop**: model → tool calls → results → model, repeated until the model stops calling tools.
- **4 tools**: search, read, write, bash. Bash is general on purpose, so the agent works out each project's
  own test command.
- **Verification tracking**: the model marks a bash call as `verification: true`. The loop tracks whether
  there are edits that haven't been verified, and it has a cap on retries after failed checks.
- **5 ways a run can end**: `completed`, `unverified`, `blocked`, `max_turns_reached`, `error`. The exit
  code is 0 only for `completed`, so it can be used in CI.
- **Model-agnostic core**: the loop only knows a `ModelProvider` interface. Gemini is one implementation,
  called over plain REST.
- **Tested without the network**: a scripted fake model, plus a fake Gemini server for an end-to-end test.
- About 950 lines of source and 200 lines of tests. **No runtime dependencies.**

---

## 2. The big picture

```
┌──────────────────────────────────────────────────────────────────┐
│  CLI (index.ts)                                                  │
│  flags, .env, validation, printing, exit code                    │
└──────────────┬───────────────────────────────────────────────────┘
               │ new AgentLoop({ provider, repoRoot, ..., onEvent })
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  AgentLoop (agent/loop.ts)            + system prompt (prompt.ts)│
│  history, turns, verification state, how a run ends              │
└───────┬──────────────────────────────────────────┬───────────────┘
        │ generateTurn(system, history, tools)     │ tools.run(name, args, {repoRoot})
        ▼                                          ▼
┌─────────────────────────────┐    ┌───────────────────────────────┐
│  ModelProvider (interface)  │    │  ToolRegistry (registry.ts)   │
│  llm/provider.ts            │    │  look up, check args, catch   │
│        ▲                    │    │  errors                       │
│        │ implements         │    └──┬──────┬──────┬──────┬───────┘
│  GeminiProvider (gemini.ts) │       ▼      ▼      ▼      ▼
│  convert format, fetch,     │    search  read   write   bash
│  retry                      │       └──────┴──┬───┘      │
└──────────────┬──────────────┘                 ▼          ▼
               ▼                       util.ts (path guard, truncate)
        Gemini REST API                 file system       shell
```

**The layers, and why they're split this way:**

| Layer | Knows about | Doesn't know about |
|---|---|---|
| CLI | Everything, because it wires the parts together | — |
| Loop | Messages, tools (by name), verification rules | Gemini, HTTP, the file system |
| Provider interface | Common message types | Tools' internals |
| Gemini provider | Gemini's format and HTTP | The loop's rules |
| Registry | Tool lookup and argument checking | Models |
| Tools | The file system and shell | Models and the loop |

Every arrow points **down**. The lower layers never import the upper ones. That's why the loop can be
tested with a fake model, and tools can be tested without any loop.

---

## 3. What happens in one run, step by step

This example comes from the end-to-end test: "fix add" in a repo where `add` does `a - b`.

```
history = [ user: "fix add" ]

Turn 1  model → codebase_search("add")               tool → "math.js:1: exports.add = ..."
Turn 2  model → read_file(math.js)                   tool → file contents
              + bash("node test.js", verification)    tool → exit 1          failedVerifications = 1
Turn 3  model → write_file(math.js, "a + b")         tool → "Overwrote"      hasUnverifiedEdits = true
Turn 4  model → bash("node test.js", verification)   tool → exit 0          counter reset, edits verified
Turn 5  model → "Fixed add()." (no tool calls)       → no unverified edits → status: completed
```

**Each turn, in detail:**
1. The loop sends **system prompt + full history + tool definitions** to the provider.
2. The provider converts that to Gemini's format, POSTs it (retrying on 429/503), and converts the reply
   back into a `ModelTurn { text, toolCalls, stopReason }`.
3. The loop adds the reply to the history.
4. If there are no tool calls, the loop decides how the run ends (or sends the model back once to verify).
5. Otherwise, it runs each tool call **one after another** through the registry, adds each result to the
   history as a `tool` message, and updates the verification state.
6. Then it repeats.

**Memory:** the model remembers nothing between calls. **The `history` array is the agent's only memory**,
which is why the whole thing is sent every turn.

---

## 4. System design of each part

For each part: what it does, its inputs and outputs, the key decisions, and what those decisions cost.

### 4.1 CLI: `index.ts`

**What it does:** it turns a shell command into a configured `AgentLoop`, runs it, prints progress, and sets the exit code.

- **Input:** `--prompt`, `--repo`, `--model`, `--max-turns`, `--max-verify-retries`, plus `GEMINI_API_KEY`
  and `GEMINI_MODEL` from the shell or `.env`.
- **Output:** progress on stdout, a final summary, and exit code 0 (`completed`) or 1 (anything else).

**Decisions:**
- **It's the one place where concrete parts are wired together** (the "composition root"). The loop never
  creates a `GeminiProvider` itself. It's handed one (**dependency injection**).
- **Progress is reported through events** (`onEvent: printEvent`). The loop doesn't print. It emits events
  and the CLI decides how to show them. A web UI could use the same events later.
- **`.env` is found next to the agent** (`import.meta.url`), not in the target repo. So it works from any
  folder, and it never reads the target repo's secrets. Variables in the shell take priority.
- **All input is checked before running** (key, repo folder, whole numbers), so the user gets a clear
  error and not a crash halfway through.
- **The exit code is 0 only for `completed`**, so scripts and CI can rely on it.
- **`process.exitCode` and not `process.exit()`**, so output isn't cut off.

**Costs:** the argument parser is hand-written (no library). Unknown flags are ignored, and a flag with no
value can slip through (`--model` as the last argument).

### 4.2 Agent loop: `agent/loop.ts` (the heart of the project)

**What it does:** it runs the model ↔ tools cycle and decides **how the run ends**.

- **Input:** a task string.
- **Output:** `{ status, finalText, turnsUsed, history }`.

**What it keeps track of:**

| Variable | Meaning |
|---|---|
| `history` | The whole conversation. It's also the agent's memory |
| `hasUnverifiedEdits` | Set by a successful `write_file`. Cleared by a passing verification |
| `failedVerifications` | Verification failures **in a row**. Reset by a pass |
| `nudgedToVerify` | Whether the model has been sent back once to verify |
| `mustStop` | The retry cap was hit, so the next reply ends the run |

**How a run ends** (every exit):
```
                         model call throws / stopReason "error" ──► error
                                          │
         ┌──────────── reply ◄────────────┘
         │
 mustStop set? ─────────────────────────────────────────────────► blocked
         │ no
 no tool calls? ── no unverified edits ─────────────────────────► completed
         │         unverified + already nudged ─────────────────► unverified
         │         unverified + not yet nudged ── add VERIFY_NUDGE, next turn
         │ has tool calls
 run tools → verification fails > maxVerifyRetries ── mustStop, add STOP_MESSAGE
         │
 turn > maxTurns ───────────────────────────────────────────────► max_turns_reached
```

**Decisions (these are the ones interviewers ask about):**
1. **"Done" is checked by code, not only asked for in the prompt.** The prompt *asks* the model to verify.
   The loop *checks* that it did. Models often claim success without checking.
2. **The model is sent back only once.** A second stop without verifying ends as `unverified`. This gives
   the model one fair chance, and it can't loop forever. (Some projects have no tests, and the model should
   be able to say so.)
3. **The retry cap is separate from the turn cap.** Without it, one stubborn failure could use up all 25
   turns. With it, the agent stops early and **explains what's blocking it** (`blocked` plus a report).
   That's more useful than silently running out of turns.
4. **Only verification that the model marks counts.** A failing `ls` or `grep` isn't a failed check.
   The downside: the model decides what counts (see 7.3).
5. **Cut-off replies (`stopReason: "length"`) never run their tools.** A half-sent `write_file` would
   corrupt a file. Every call still gets a result (a fake error), because the API needs one result per call.
6. **Message order is kept valid.** `STOP_MESSAGE` is added only **after** all the tool results of that
   turn, so every call is still directly followed by its result.
7. **There's a turn cap (25).** The agent runs unattended, so it needs a hard limit on cost and time.
   (pi has none, because a person is watching it.)
8. **Tools run one after another, not in parallel.** That's simpler, gives a clear order, and avoids two
   writes racing each other. The cost is speed when there are several independent reads.

### 4.3 System prompt: `agent/prompt.ts`

**What it does:** it holds the agent's standing instructions: search → read → write whole files → verify
→ retry N times → finish in plain text.

**Decision:** the prompt and the code **say the same thing**. The prompt describes the rules, and the loop
enforces the important ones. The retry count is inserted from the config, so they can't drift apart.

**Principle:** use the prompt for guidance, and code for guarantees. "Search before guessing paths" can
only be a request. "Verify before finishing" is enforced.

### 4.4 Provider interface: `llm/provider.ts`

**What it does:** it defines the common types (`Message`, `ToolCall`, `ModelTurn`) and one method:
```ts
generateTurn(systemPrompt, history, tools): Promise<ModelTurn>
```

**Decisions:**
- **The loop works only with these types.** Each vendor's format is converted at the edge (the
  **adapter pattern**). Adding Claude or OpenAI means writing one new file. The loop doesn't change.
- **`stopReason` is normalised to `stop | length | error`.** Every vendor has its own reasons, and the
  loop only needs to know these 3 outcomes.
- **`providerMetadata: unknown`** is a place to keep vendor data that has to come back unchanged, such as
  Gemini's `thoughtSignature`. The loop keeps it without understanding it.
- **Structural typing** means any object with a matching `generateTurn` is a provider. That's how the
  tests plug in a fake model in one line.

### 4.5 Gemini provider: `llm/gemini.ts`

**What it does:** it converts to and from Gemini's REST format, and handles HTTP and retries.

**Decisions:**
- **REST with `fetch`, no SDK.** There are no dependencies, the request and response format can be read
  in one file, and it's easy to test by faking `fetch`. Cost: the response types are written by hand and
  not checked at runtime, and new API changes have to be followed by hand.
- **Converting the history** (`toGeminiContents`):
  - `assistant` becomes `model`. `tool` results become `functionResponse` parts inside a **`user`**
    content. Gemini has only 2 roles.
  - Consecutive contents with the same role are **merged**, because Gemini wants the roles to alternate
    and all the results of one turn together.
  - Empty contents are dropped, because Gemini rejects them.
  - `thoughtSignature` is sent back with each function call, because thinking models require it.
- **Retries:**
  - 429 (rate limit) and 503 (overloaded) are retried, up to 6 attempts in total.
  - The wait uses the server's `retryDelay` if it sends one. Otherwise it's **exponential backoff**
    (2, 4, 8, 16, 30s) plus **random jitter** of up to 1s.
  - A **used-up daily quota fails at once**, because waiting seconds won't fix a daily limit, so it's
    better to fail fast with a clear hint.
  - Any other error (400, 401, 404) fails at once.
- **The API key goes in a header, not the URL**, because URLs end up in logs. A test checks this.
- **Gemini doesn't give tool calls ids**, so the provider creates UUIDs. Gemini matches results to calls
  by name and order.

### 4.6 Tool registry: `tools/registry.ts`

**What it does:** it keeps a map from name to tool, gives the model the tool list, and runs a tool by name.

**Decisions:**
- **`run()` never throws.** An unknown tool, bad arguments, or a tool crash all become
  `{ ok: false, output: "..." }`. **Errors are data**, sent back to the model so it can fix its own
  mistake (a typo in a tool name, a missing argument). One bad call doesn't end the run.
- **Arguments are checked against the schema before running** (required fields and top-level types).
  The model gets a precise message ("`path` must be a string, got number") and not a confusing crash
  inside the tool.
- **Tools can be plugged in** (`new ToolRegistry(tools)`), and all four are used by default.

**Costs:** the check is shallow. It doesn't cover nested fields, `enum`, or array items.

### 4.7 The tools

All four follow the same `Tool` contract: `definition` (what the model sees) plus `execute(args, ctx)`
(what happens). `ctx.repoRoot` comes from the **agent, not the model**, so the model can't choose which
folder counts as the repo.

| Tool | Design points | Limits |
|---|---|---|
| **`codebase_search`** | Walks the folders recursively. Matches **file names and lines**, ignoring case. Keywords are escaped, and regex is optional. Skips hidden folders (`.git`, `.env`) and generated ones (`node_modules`, `dist`, …). An unreadable file gives no lines instead of stopping the search. | 50 matching lines, 5000 files, files over 1 MB not read, 20 file names shown |
| **`read_file`** | Line-numbered output. **Splits long files into parts at whole lines**, with an `offset=N` footer for the next part. `offset`/`limit` read any range. A folder path lists the folder. | 8000 characters per call |
| **`write_file`** | Rewrites the **whole file**. Creates missing folders. Says whether the file was created or overwritten. | Not atomic, and there's no undo (git is the safety net) |
| **`bash`** | `spawn` with a shell, in the repo folder. Timeout with SIGKILL. **Blocklist** of destructive commands. Returns the exit code plus stdout and stderr, each shortened. `ok = exit 0 && not timed out`. | 60s default, 300s max, 4000 characters per stream |

**Why these 4 tools:** they're the smallest set that covers the whole job. Find (search), understand
(read), change (write), check (bash). Bash is **general** instead of a fixed "run tests" tool, because
every project checks itself differently (`npm test`, `pytest`, `cargo test`, `tsc --noEmit`).

**Why whole-file writes:** it's the simplest tool to build and to explain. The cost is tokens (the model
re-sends the whole file), and the risk that it drops code it didn't mean to touch. That's why "an edit
tool" is next step #1.

### 4.8 Shared helpers: `tools/util.ts`

- **`resolveInRepo`**: makes a path absolute and rejects anything outside the repo. It compares against
  `root + "/"` so that `/repo-evil` doesn't pass as `/repo`. It **doesn't follow symlinks**.
- **`truncate`**: keeps the first 70% and the last 30% of the budget. Errors and test summaries show up
  at the **end** of output, so the end is always kept.

### 4.9 Tests: `agent.test.ts`

**Strategy:** test the **real loop and the real tools**, and fake only what's non-deterministic or
external (the model and the network).

| Level | How |
|---|---|
| Loop logic | A scripted fake model replays turns. Every way a run can end is covered, plus the retry cap and cut-off replies |
| Tools | Called directly through the registry in a temporary folder. Covers the guards, search, and reading in parts |
| Gemini client | `fetch` is faked: retry reporting, daily quota failing at once, converting history |
| End to end | The real `GeminiProvider` and a real loop fix a real bug against a **fake Gemini server**, which also checks every request follows Gemini's format rules |

- **Network guard:** `globalThis.fetch` is replaced with a function that throws, so a test can never
  spend API credits.
- **Built-in runner** (`node:test`), so there are no test dependencies.
- **Not tested:** CLI argument parsing and printing, bash timeouts, search limits.

---

## 5. Concerns that cut across the whole system

### 5.1 Context and tokens
- The history is sent **in full every turn**, so the cost grows as the conversation grows (turn N re-sends
  turns 1..N-1). The 25-turn cap and the output limits keep it bounded.
- Ways it's kept small: search before reading, 8000 characters per read, 4000 per bash stream, 50 search
  matches, and shortened output that keeps the end.
- **Not built:** summarising or dropping old turns, and prompt caching.

### 5.2 Handling errors: three kinds, three reactions

| Kind | Example | Reaction |
|---|---|---|
| The model's mistake | Wrong tool name, bad arguments, file not found, failing test | **Sent back as a tool result.** The model fixes it |
| A passing problem | 429 or 503 from Gemini | **Retry with backoff** inside the provider |
| Fatal | Bad key, daily quota used up, blocked prompt, malformed call | **End the run with `error`** and a clear message |

### 5.3 Safety (guard rails, **not a sandbox**)
- Path guard on read, write and search.
- Hidden files (including `.env`) are skipped by search.
- Bash: blocklist, timeout, output limits, runs in the repo folder.
- API key in a header, never in the URL. `.env` is in `.gitignore`.
- **Honest gaps:** bash runs with **your user's full permissions**. The blocklist is easy to get around
  (`rm -r -f /`, `git push -f`). Symlinks can point outside the repo. A timeout kills the shell but not
  always the programs it started. **A real fix is a container sandbox (Docker).**

### 5.4 Observability
- The loop emits typed events (`turn_start`, `tool_call`, `tool_result`, `verification_*`), and the CLI
  prints them.
- The full `history` is returned, so a run can be inspected afterwards.
- **Not built:** tracking tokens or cost, timing, structured logs.

### 5.5 Configuration
Everything that can be tuned has a default: turns 25, retries 3, model `gemini-2.0-flash`. The limits
inside the tools are constants in their files.

---

## 6. Key numbers

| What | Value | Where |
|---|---|---|
| Max turns | 25 | loop, CLI |
| Verify retries | 3 (4 attempts in total) | loop, CLI |
| Gemini attempts | 6, with backoff 2→30s plus jitter | gemini.ts |
| Read part size | 8000 characters | read.ts |
| Bash timeout | 60s default, 300s max, 1s min | bash.ts |
| Bash output | 4000 characters per stream | bash.ts |
| Search | 50 lines, 20 names, 5000 files, 1 MB/file | search.ts |
| Size | ~950 lines of source, ~200 lines of tests, 0 runtime deps | — |

---

## 7. Trade-offs and limitations (say these before they're asked)

1. **Whole-file writes.** Expensive on big files, and the model can drop code by accident. The fix is a
   find-and-replace edit tool.
2. **A passing check is only as good as the check.** If the project has weak tests, "completed" means
   little.
3. **The model decides what counts as verification.** It could mark `echo ok` as `verification: true`.
   The loop trusts that flag. A stronger design would let the **user set the verification command**, or
   detect it from `package.json` and similar files.
4. **Edits made through bash aren't tracked.** `sed -i` or `echo > file` change files without setting
   `hasUnverifiedEdits`. The fix: check `git status` or file hashes before and after each command.
5. **No sandbox.** See 5.3.
6. **One provider.** The interface exists, but only Gemini is implemented.
7. **No memory between runs, and old turns are never compacted.** Long tasks hit the turn cap or the
   model's context limit.
8. **Tools run one at a time.** Several reads in one turn could run in parallel.

---

## 8. How to extend or scale it (the "what would you do next" answer)

| Goal | Change |
|---|---|
| Cheaper, safer edits | An `edit_file(path, old, new)` tool that requires `old` to appear exactly once |
| Real safety | Run bash inside a Docker container with only the repo mounted, no network, and CPU/memory limits |
| Trustworthy "done" | A user-set or auto-detected verification command, and compare `git diff` before and after |
| Long tasks | Summarise old turns and keep only the latest tool outputs in full. Prompt caching |
| Speed | Run read-only tools (search, read) in parallel. Stream model output |
| Another model | One `ClaudeProvider`/`OpenAIProvider` file implementing `ModelProvider` |
| Cost visibility | Record token usage from each response, and report it per run |
| Quality | An evaluation set of real tasks in 1000+ line repos: completed rate, and "fixed after a failed check" rate |
| Many users or runs | A job queue, one sandbox per run, and history stored in a database so a run can be resumed |

---

## 9. Interview questions and short answers

**Q: Why a loop and not a single prompt?**
A: One prompt can't look around or check its own work. Finding files, reading them, and seeing whether a
test passes all need the model to act, see the result, and decide again.

**Q: How does the agent know when it's done?**
A: The model signals "done" by replying with no tool call. The **loop** then checks: if files were
edited and no verification passed since the last edit, it sends the model back once. If it stops again,
the status is `unverified`, not `completed`.

**Q: What stops it from running forever?**
A: Three limits: 25 turns in total, a cap on verification retries (3) after which it must report, and
bash timeouts. Gemini retries are capped at 6 attempts.

**Q: What happens when the model calls a tool wrongly?**
A: The registry catches it and returns `ok: false` with a precise message. The model sees it next turn
and corrects itself. Tool errors never crash the run.

**Q: Why send the full history every time?**
A: The API has no state and the model remembers nothing. The history *is* the memory. The cost grows each
turn, which the turn cap and output limits keep bounded.

**Q: What's `stopReason: "length"` and why does it matter?**
A: The reply hit the output-token limit, so a tool call's arguments might be cut off, like half a file.
Running it would corrupt files, so the loop skips those calls and tells the model to send them again.

**Q: How would you add Claude or OpenAI?**
A: Write one class that implements `generateTurn`: convert `Message[]` to the vendor's format, call the
API, and convert the reply to `ModelTurn`. The loop and tools don't change.

**Q: Why no Gemini SDK?**
A: There's one endpoint and no streaming, so `fetch` is about 30 lines. It adds no dependency, the wire
format is visible, and it's easy to test by faking `fetch`. The retry rules are custom (daily quota fails
at once). An SDK would save about 30–40 lines, and I'd switch if I needed streaming or more features.

**Q: How do you handle rate limits?**
A: 429 and 503 are retried with the server's `retryDelay`, or with exponential backoff plus jitter. A
daily quota error fails at once, because waiting won't help.

**Q: Is it safe to run?**
A: It has guard rails, not a sandbox. Paths are kept inside the repo, destructive commands are
blocklisted, and there are timeouts. But bash runs with the user's permissions, so the real fix is a
container. I'd only run it on trusted repos and tasks.

**Q: Why a general bash tool and not a fixed "run tests" tool?**
A: Every project checks itself differently. The model reads `package.json` or the README and picks the
command. The trade-off is that it can pick the wrong one, or a weak one.

**Q: Can the model cheat verification?**
A: Yes. It sets the `verification` flag itself, so it could mark a meaningless command. Edits through bash
also bypass the edit tracking. Fixes: a user-set verification command, and checking `git diff` or file
hashes after every command.

**Q: How did you test an LLM agent without flaky tests?**
A: I faked the model, not the logic. A scripted provider replays fixed turns through the real loop and
real tools in a temporary folder. For Gemini, I faked `fetch` and checked every request against Gemini's
format rules. Any real network call fails the tests.

**Q: Why whole-file writes?**
A: It's the simplest possible edit tool. The cost is tokens and the risk of dropping code on big files.
A find-and-replace edit tool is my first next step.

**Q: Why is the retry cap separate from the turn cap?**
A: So one stubborn failure doesn't silently use up every turn. After N failures, the agent stops and
explains what's blocking it. That report is more useful than hitting the turn limit.

**Q: Why run tools one at a time?**
A: Simpler, with a clear order, and no two writes racing on the same file. Next step: run the read-only
tools in parallel.

**Q: What's the hardest bug or edge case you handled?**
A: Good candidates:
- (1) Gemini's format rules: merging several tool results into one user content, and sending back
  `thoughtSignature`.
- (2) Cut-off replies that must not run their tools, while every call still gets a result.
- (3) Placing the stop message *after* all the tool results, so the message order stays valid.

**Q: What would you change first?**
A: 1) An edit tool. 2) A Docker sandbox. 3) A verification command the user can't have faked, plus
tracking changes by diff. 4) An evaluation set to measure success rate.

**Q: How would you measure whether it's good?**
A: Real tasks in 1000+ line repos. Measure the share completed with a passing check, the share that
failed a check first and then recovered (what the verification loop adds), and group the failures by cause.

---

## 10. TypeScript features used across the project (quick revision)

| Feature | Where | One line |
|---|---|---|
| `interface` / `type` | everywhere | Describe the shape of data |
| Union of string literals | `AgentStatus`, `stopReason` | Only these exact strings are allowed |
| Discriminated union | `Message` (`role`), `AgentEvent` (`type`) | One shared field decides which fields exist |
| Narrowing | `if (msg.role === "tool")`, `typeof x === "number"` | TS works out a more specific type |
| `unknown` | tool args, `providerMetadata` | Must be checked before use. The safe `any` |
| `Record<K, V>` | args, schemas | An object with keys K and values V |
| Optional `?`, `??`, `?.` | everywhere | Optional field, default value, safe property access |
| `import type` | loop, gemini | Imports that are removed at compile time |
| `private readonly` / parameter properties | `AgentLoop`, `GeminiProvider` | Fields that can't be changed, declared in the constructor |
| `implements` | `GeminiProvider` | Checks that a class matches an interface |
| Structural typing | fake providers in tests | Matching shape is enough, no `implements` needed |
| Getter `get` | `ToolRegistry.definitions` | Read like a property, runs code |
| `Map`, `Set` | registry, search | Key-value lookup, and membership checks |
| `async`/`await`, `Promise` | everywhere | Asynchronous code that reads top to bottom |
| `new Promise(resolve => ...)` | `runCommand`, `sleep` | Wrap events or timers as a Promise |
| `as` cast, `!` non-null assertion | catch blocks, `GEMINI_API_KEY!` | Tell the compiler something it can't check |
| Indexed access type | `GeminiContent["role"]` | Reuse the type of one field |
| `ReturnType<typeof f>` | tests | The type a function returns |
| Template strings | prompts, messages | `${}` inserts values. A `\` at a line end joins lines |

---

## 11. Map of the files

| File | Lines | Role | Details |
|---|---|---|---|
| `src/index.ts` | 164 | CLI, wiring, printing | `index.md` |
| `src/agent/loop.ts` | 160 | The agent loop and how a run ends | `loop.md` |
| `src/agent/prompt.ts` | 23 | System prompt | `prompt.md` |
| `src/llm/provider.ts` | 31 | Model-agnostic types and interface | `provider.md` |
| `src/llm/gemini.ts` | 158 | Gemini REST adapter and retries | `gemini.md` |
| `src/tools/types.ts` | 31 | Tool contracts | `types.md` |
| `src/tools/registry.ts` | 53 | Lookup, argument checks, never throws | `registry.md` |
| `src/tools/search.ts` | 102 | `codebase_search` | `search.md` |
| `src/tools/read.ts` | 66 | `read_file` | `read.md` |
| `src/tools/write.ts` | 39 | `write_file` | `write.md` |
| `src/tools/bash.ts` | 105 | `bash` | `bash.md` |
| `src/tools/util.ts` | 23 | Path guard, truncate | `util.md` |
| `src/agent.test.ts` | 197 | Tests | `agent.test.md` |
