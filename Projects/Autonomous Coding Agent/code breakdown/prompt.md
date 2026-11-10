# Deep dive: `src/agent/prompt.ts`

**What it does in one line:** it builds the system prompt, the standing instructions sent with every model call, and inserts the retry limit into it.

The file has one function.

---

## `buildSystemPrompt(maxVerifyRetries)` (L1–23)

```ts
export function buildSystemPrompt(maxVerifyRetries: number): string {
  return `You are a coding agent ... Make the change the user \
asks for; don't just describe it.
...
You get ${maxVerifyRetries} \
retries. ...`;
}
```
> **TS basics**
> - The whole prompt is **one template string** (backticks). Template strings can span several lines, and each real line break becomes `\n` in the string.
> - A **`\` at the end of a line** inside a template string removes that line break. The source stays readable at about 120 characters per line, while the model sees one long line. Lines that **don't** end in `\` keep their break, which is how the numbered list and paragraphs are formed.
> - `${maxVerifyRetries}` inserts the number, so the prompt always matches the loop's actual setting.

`loop.ts` calls it once per `run()`, and the result is sent on **every** turn.

---

## What the prompt tells the model

It opens by saying who the model is: a coding agent working through tools. It must **make** the change, not only describe it.

**How to work (the 6 steps):**

| # | Instruction | Enforced in code by |
|---|---|---|
| 1 | Find files with `codebase_search`, and don't guess paths | Only the prompt |
| 2 | Read before editing, and keep reading with `offset` until you have the whole file | The `read_file` footer gives the next offset |
| 3 | Edit with `write_file`, always with the complete content | Only the prompt, plus the tool description |
| 4 | Verify with bash and `verification: true`. It only counts once a run passes **after the last edit** | `loop.ts`: `hasUnverifiedEdits` and `VERIFY_NUDGE` |
| 5 | When verification fails, fix and retry, up to N retries, then stop and report | `loop.ts`: `failedVerifications` and `STOP_MESSAGE` |
| 6 | Finish by replying in plain text with no tool call | `loop.ts`: `toolCalls.length === 0` ends the run |

**Rules:**
- Only edit code you have actually read, and never invent paths or contents.
- Make the smallest change that does the job.
- If the project has no tests, type-checker or build, say so, and don't claim the change is verified.
- Turns are limited, so don't re-read files or re-run commands when nothing has changed.

---

## How it connects
The prompt **asks** for good behaviour, and `loop.ts` **enforces** the important parts: verifying after edits, the retry cap, and what counts as finishing. Steps 1–3 and the rules are guidance the code can't check.
