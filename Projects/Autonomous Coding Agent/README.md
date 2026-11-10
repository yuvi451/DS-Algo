# Autonomous Coding Agent

A small coding agent written in TypeScript. You give it a task in plain English and a repository. It finds
the right files, edits them, runs the project's own tests to check its work, and fixes its mistakes until the
tests pass.

It is a from-scratch take on the core idea behind terminal coding agents like [pi](https://github.com/earendil-works/pi):
a small loop and a few sharp tools. It is small enough to read end to end in one sitting.

## How it works

```
 task ──► Agent loop ──► Gemini ──► tool calls ──► Tools ──► repository
             ▲                                       │
             └──────────── tool results ◄────────────┘
```

Each turn, the loop sends the model the whole conversation so far. The model either asks for tools or
replies in plain text. The loop runs the tools, adds their results to the conversation, and goes again.

The model has no memory between API calls. **The conversation history kept by the loop is the agent's
memory**, which is why it is sent in full every turn.

The loop follows the same core rules as pi's agent loop:

- A reply with no tool call ends the run.
- Tool arguments are checked against the tool's schema before the tool runs. Bad arguments, unknown tools,
  and tool crashes are sent back to the model as errors, so it can correct itself.
- If a reply was cut off by the model's output limit, its tool calls are **not** run, because their
  arguments may be cut off too (think half a file passed to `write_file`). The model is told to send them again.
- If the model request fails, or the model stops with an error (for example a blocked prompt or a
  malformed tool call), the run ends with status `error`.

### Tools

| Tool | What it does |
|---|---|
| `codebase_search` | Searches file names and contents for a keyword or regex, so the agent finds files instead of guessing paths. |
| `read_file` | Returns a file with line numbers (or lists a folder). Long files come back in parts: each part ends with the `offset` to read the next one, and `offset`/`limit` can read any range of lines. |
| `write_file` | Creates or overwrites a whole file. |
| `bash` | Runs a shell command in the repo and returns the exit code and output. The agent uses it to run tests, type-checks, and builds. |

### Verification and retries

The agent has to prove its edits work before it can finish:

- When the agent runs a check (tests, type-check, lint, build), it marks the `bash` call with
  `verification: true`. Only those runs count. A failing `ls` or `grep` is not a failed check.
- **Finishing.** The run ends when the model replies without asking for a tool. If it edited files and
  no check has passed since its last edit, the loop sends it back once to run one. If it stops again
  without a passing check, the run ends as `unverified` instead of `completed`.
- **Retries.** After a failed check, the agent gets 3 retries (4 attempts in total). If the check still
  fails, the loop tells it to stop and explain what is blocking it, and the run ends as `blocked`.
- **Turn limit.** A run can take at most 25 turns. If it hits that, it ends as `max_turns_reached`.
  (pi has no turn limit, because a person is watching it. This agent runs unattended, so it needs one.)

### Safety

- `read_file`, `write_file`, and `codebase_search` refuse paths outside the repository.
- `bash` has a timeout, cuts long output short, and blocks obviously destructive commands (`rm -rf /`,
  fork bombs, `curl … | sh`, force-push, and so on).

These are guard rails, **not a sandbox**. `bash` runs with your user's permissions. Only use the agent on
tasks and repositories you trust.

## Usage

Needs Node.js 20.12 or newer.

```bash
npm install
npm run build
cp .env.example .env                   # then put your Gemini API key in .env

node dist/index.js --prompt "add input validation to the signup endpoint" --repo /path/to/repo
```

Quote any path with spaces (`--repo "/Users/me/My Project"`), and keep the command on one line. If you
split it with `\`, make sure nothing (not even a space) comes after the `\`, or the rest of the command
is dropped.

| Flag | Meaning | Default |
|---|---|---|
| `-p, --prompt` | The task (required, can't be blank) | — |
| `-r, --repo` | The repository to work on | current folder |
| `--model` | Gemini model name | `$GEMINI_MODEL`, else `gemini-2.0-flash` |
| `--max-turns` | Most turns the agent may take | 25 |
| `--max-verify-retries` | Retries after a failed check | 3 |

The CLI reads `GEMINI_API_KEY` and `GEMINI_MODEL` from the `.env` file in the agent's folder (not the
target repo's). Variables set in your shell take priority. `.env` is in `.gitignore`, so the key is never
committed.

While it runs, the CLI prints each turn: what the model said, which tools it called, and a short preview of
each result. If Gemini is rate limited or overloaded (429/503), it prints a `… retrying in Ns` line and waits,
up to 6 attempts. A used-up **daily** quota fails at once instead, since waiting a few seconds won't fix it.
At the end it prints the status (`completed`, `unverified`, `blocked`, `max_turns_reached`,
or `error`) and the agent's final message. The exit code is 0 only for `completed`.

## Tests

```bash
npm test
```

The tests run the real loop and tools against a temporary folder, with a fake model that replays a fixed
list of replies. They cover every way a run can end, the retry limit, cut-off replies, argument checks, the
path and command guards, search, reading long files in parts, and the Gemini client's retry handling. One test runs a full task through the real Gemini client against a
fake Gemini API, and checks that every request follows Gemini's format rules.

The tests never touch the network: any real API call fails the test run, so running them can never
use your API key.

## Project layout

```
src/
  index.ts            CLI: reads flags, prints progress, sets the exit code
  agent.test.ts       Tests
  agent/
    loop.ts           The agent loop: turns, verification tracking, retry limit, how a run ends
    prompt.ts         The system prompt (the agent's instructions)
  llm/
    provider.ts       Model-agnostic message types and the ModelProvider interface
    gemini.ts         Gemini provider: calls the REST API directly, no SDK
  tools/
    types.ts          Tool interfaces
    registry.ts       Looks up a tool by name and runs it
    search.ts         codebase_search
    read.ts           read_file
    write.ts          write_file
    bash.ts           bash
    util.ts           Keeps paths inside the repo, trims long output
```

## Design choices

- **A loop, not a single prompt.** One prompt can't find the right files or check whether a fix worked.
  That needs the model to act, look at the result, and decide what to do next.
- **Search, then read.** The agent pulls in only the files it needs instead of the whole repo, which
  keeps the context small and focused.
- **A general `bash` tool instead of a fixed "run tests" command.** Every project checks itself
  differently (`npm test`, `pytest`, `tsc --noEmit`, …). The agent works out the right command itself. The
  cost is that it can pick the wrong one.
- **A separate retry limit.** Without it, one stubborn bug could use up the whole turn budget. The limit
  makes the agent stop and report the problem instead.
- **The finish check is enforced by code, not just the prompt.** The prompt asks the model to verify, and
  the loop checks that it actually did.
- **No SDK for Gemini.** Calling the REST API directly keeps the request and response format visible in
  one file.
- **A provider interface.** The loop only knows about `ModelProvider`, so another model can be added
  without touching the loop. The tests use this to swap in a fake model.

## Limitations

- **Whole-file writes.** `write_file` replaces the full file. That uses a lot of tokens on big files, and
  the model can accidentally drop code it didn't mean to touch. To edit a long file, the model first has
  to read every part of it.
- **A passing check is only as good as the check.** The loop can confirm that a check passed after the last
  edit, but not that the check actually tests the change. A project with few tests gives a weak signal.
- **No sandbox.** See Safety above.
- **One provider.** Only Gemini is implemented.
- **No memory between runs.** Each run starts from scratch.

## Next steps

1. **An edit tool** that replaces a specific piece of text instead of the whole file. It is cheaper,
   safer on big files, and easier for the agent when fixing a failed check.
2. **A real sandbox** for `bash`, e.g. running commands in a Docker container.
3. **A second model provider**, to prove the loop doesn't depend on Gemini.

## Evaluating it

The plan: run the agent on a set of real tasks (features, bug fixes, small refactors) in repositories of
1,000+ lines, and report:

- how many tasks it finished with a passing check, and
- how many of those failed a check at first and were fixed on a retry. These are the tasks the
  verification loop made possible.

The failures matter too: why each one failed (an unclear task, a file search didn't find) says more than
the success rate alone.
