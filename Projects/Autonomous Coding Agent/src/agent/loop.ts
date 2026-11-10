import type { Message, ModelProvider, ModelTurn } from "../llm/provider.js";
import { ToolRegistry } from "../tools/registry.js";
import type { ToolResult } from "../tools/types.js";
import { buildSystemPrompt } from "./prompt.js";

/**
 * `unverified`: the model finished after editing files, but no verification run passed after its last edit.
 * `error`: the model request failed, or the model stopped with an error.
 */
export type AgentStatus = "completed" | "unverified" | "blocked" | "max_turns_reached" | "error";

export interface AgentRunResult {
  status: AgentStatus;
  finalText: string;
  turnsUsed: number;
  history: Message[];
}

export type AgentEvent =
  | { type: "turn_start"; turn: number }
  | { type: "assistant_text"; text: string }
  | { type: "tool_call"; name: string; arguments: Record<string, unknown> }
  | { type: "tool_result"; name: string; ok: boolean; output: string }
  | { type: "verification_failed"; retry: number; maxRetries: number }
  | { type: "verification_cap_reached"; maxRetries: number }
  | { type: "verification_required" };

export interface AgentLoopConfig {
  provider: ModelProvider;
  repoRoot: string;
  maxTurns?: number;
  /** Retries allowed after a failed verification run, so maxVerifyRetries + 1 attempts in total. */
  maxVerifyRetries?: number;
  tools?: ToolRegistry;
  onEvent?: (event: AgentEvent) => void;
}

const VERIFY_NUDGE =
  "You edited files, but no verification run has passed since your last edit. Run the project's verification " +
  "command now with bash and verification: true. If the project has no tests, type-checker, or build, reply in " +
  "plain text and say so.";

const STOP_MESSAGE =
  "Verification has failed too many times. Stop trying to fix it. Reply now in plain text, with no tool call: " +
  "what you tried, the current error, and what is blocking you.";

// Like pi: a reply cut off by the output limit may carry cut-off arguments (e.g. half a file), so none of its
// tool calls are run. The model gets this error instead and can send them again.
const CUT_OFF_RESULT: ToolResult = {
  ok: false,
  output: "Not run: your reply hit the output limit, so this call's arguments may be cut off. Send it again in full.",
};

export class AgentLoop {
  private readonly provider: ModelProvider;
  private readonly repoRoot: string;
  private readonly maxTurns: number;
  private readonly maxVerifyRetries: number;
  private readonly tools: ToolRegistry;
  private readonly emit: (event: AgentEvent) => void;

  constructor(config: AgentLoopConfig) {
    this.provider = config.provider;
    this.repoRoot = config.repoRoot;
    this.maxTurns = config.maxTurns ?? 25;
    this.maxVerifyRetries = config.maxVerifyRetries ?? 3;
    this.tools = config.tools ?? new ToolRegistry();
    this.emit = config.onEvent ?? (() => {});
  }

  async run(task: string): Promise<AgentRunResult> {
    const systemPrompt = buildSystemPrompt(this.maxVerifyRetries);
    const history: Message[] = [{ role: "user", content: task }];

    let failedVerifications = 0;
    let hasUnverifiedEdits = false;
    let nudgedToVerify = false;
    let mustStop = false;
    let lastText = "";

    for (let turn = 1; turn <= this.maxTurns; turn++) {
      this.emit({ type: "turn_start", turn });

      // The model keeps no state between calls, so every turn sends the full history.
      let reply: ModelTurn;
      try {
        reply = await this.provider.generateTurn(systemPrompt, history, this.tools.definitions);
      } catch (err) {
        return this.finish("error", `Model request failed: ${(err as Error).message}`, turn, history);
      }
      if (reply.stopReason === "error") {
        return this.finish("error", reply.errorMessage ?? "The model stopped with an error.", turn, history);
      }

      const { text, toolCalls, stopReason } = reply;
      history.push({ role: "assistant", content: text, toolCalls });
      if (text) this.emit({ type: "assistant_text", text });
      lastText = text;

      // After the retry cap we already asked for a final report, so this reply ends the run.
      if (mustStop) {
        return this.finish("blocked", text || "Verification kept failing; the model gave no report.", turn, history);
      }

      if (toolCalls.length === 0) {
        if (!hasUnverifiedEdits) return this.finish("completed", text, turn, history);
        if (nudgedToVerify) return this.finish("unverified", text, turn, history);
        nudgedToVerify = true;
        this.emit({ type: "verification_required" });
        history.push({ role: "user", content: VERIFY_NUDGE });
        continue;
      }

      for (const call of toolCalls) {
        this.emit({ type: "tool_call", name: call.name, arguments: call.arguments });
        const result =
          stopReason === "length"
            ? CUT_OFF_RESULT
            : await this.tools.run(call.name, call.arguments, { repoRoot: this.repoRoot });
        this.emit({ type: "tool_result", name: call.name, ok: result.ok, output: result.output });
        history.push({
          role: "tool",
          toolCallId: call.id,
          toolName: call.name,
          content: result.output,
          isError: !result.ok,
        });

        if (stopReason === "length") continue;
        if (call.name === "write_file" && result.ok) hasUnverifiedEdits = true;

        // Only bash runs the model marked as verification count. A failing `ls` or `grep` is not a failed check.
        if (call.name !== "bash" || call.arguments.verification !== true) continue;

        if (result.ok) {
          failedVerifications = 0;
          hasUnverifiedEdits = false;
        } else {
          failedVerifications++;
          if (failedVerifications <= this.maxVerifyRetries) {
            this.emit({ type: "verification_failed", retry: failedVerifications, maxRetries: this.maxVerifyRetries });
          } else if (!mustStop) {
            this.emit({ type: "verification_cap_reached", maxRetries: this.maxVerifyRetries });
            mustStop = true;
          }
        }
      }

      // Added after all tool results, so every tool call in this turn still gets its answer first.
      if (mustStop) history.push({ role: "user", content: STOP_MESSAGE });
    }

    const fallback = `Hit the ${this.maxTurns}-turn limit before the task was finished.`;
    return this.finish("max_turns_reached", lastText || fallback, this.maxTurns, history);
  }

  private finish(status: AgentStatus, finalText: string, turnsUsed: number, history: Message[]): AgentRunResult {
    return { status, finalText, turnsUsed, history };
  }
}
