import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { AgentLoop } from "./agent/loop.js";
import { GeminiProvider, toGeminiContents } from "./llm/gemini.js";
import type { Message, ModelTurn } from "./llm/provider.js";
import { ToolRegistry } from "./tools/registry.js";

// Tests must never reach a real API. Tests that need Gemini replace fetch with a fake.
globalThis.fetch = async () => {
  throw new Error("Tests must not make network calls.");
};

const tempRepo = () => fs.mkdtemp(path.join(os.tmpdir(), "aca-"));

/** Runs the real loop and tools, but the "model" just replays a fixed list of turns. */
async function run(turns: ModelTurn[], repoRoot?: string) {
  const provider = { generateTurn: async () => turns.shift() ?? reply("out of turns") };
  return new AgentLoop({ provider, repoRoot: repoRoot ?? (await tempRepo()), maxVerifyRetries: 3 }).run("task");
}

const reply = (text: string): ModelTurn => ({ text, toolCalls: [], stopReason: "stop" });
let callId = 0;
const call = (name: string, args: Record<string, unknown>): ModelTurn => ({
  text: "",
  toolCalls: [{ id: String(++callId), name, arguments: args }],
  stopReason: "stop",
});
const edit = () => call("write_file", { path: "a.txt", content: "hi" });
const verify = (command: string) => call("bash", { command, verification: true });
const done = reply("done");

test("finishing without edits is completed", async () => {
  assert.equal((await run([done])).status, "completed");
});

test("edit followed by a passing verification is completed", async () => {
  assert.equal((await run([edit(), verify("true"), done])).status, "completed");
});

test("finishing with unverified edits is pushed back once, then marked unverified", async () => {
  const result = await run([edit(), done, done]);
  assert.equal(result.status, "unverified");
  assert.equal(result.turnsUsed, 3);
});

test("verifying after the push-back is completed", async () => {
  assert.equal((await run([edit(), done, verify("true"), done])).status, "completed");
});

test("a failed verification does not count as verified", async () => {
  assert.equal((await run([edit(), verify("false"), done, done])).status, "unverified");
});

test("3 retries allow 4 failed runs before blocking; failing non-verification commands don't count", async () => {
  const inspect = call("bash", { command: "false" });
  const fail = () => verify("false");

  const blocked = await run([edit(), inspect, fail(), fail(), fail(), fail(), done]);
  assert.equal(blocked.status, "blocked");
  assert.equal(blocked.turnsUsed, 7);

  const recovered = await run([edit(), fail(), fail(), fail(), verify("true"), done]);
  assert.equal(recovered.status, "completed");
});

test("a model error or failed request ends the run with status error", async () => {
  const errorTurn: ModelTurn = { text: "", toolCalls: [], stopReason: "error", errorMessage: "MALFORMED_FUNCTION_CALL" };
  assert.equal((await run([errorTurn])).status, "error");

  const failing = { generateTurn: async (): Promise<ModelTurn> => { throw new Error("503"); } };
  const result = await new AgentLoop({ provider: failing, repoRoot: await tempRepo() }).run("task");
  assert.equal(result.status, "error");
  assert.match(result.finalText, /503/);
});

test("tool calls in a reply cut off by the output limit are not run", async () => {
  const repoRoot = await tempRepo();
  const cutOff: ModelTurn = { ...edit(), stopReason: "length" };
  const result = await run([cutOff, done], repoRoot);
  assert.equal(result.status, "completed");
  await assert.rejects(fs.access(path.join(repoRoot, "a.txt")));
  assert.ok(result.history.some((m) => m.role === "tool" && m.isError && m.content.includes("output limit")));
});

test("tools reject bad arguments, paths outside the repo, and destructive commands", async () => {
  const tools = new ToolRegistry();
  const ctx = { repoRoot: await tempRepo() };
  const missing = await tools.run("write_file", { path: "a.txt" }, ctx);
  assert.match(missing.output, /"content" is required/);
  const wrongType = await tools.run("read_file", { path: 5 }, ctx);
  assert.match(wrongType.output, /"path" must be a string/);
  assert.equal((await tools.run("read_file", { path: "../x" }, ctx)).ok, false);
  assert.equal((await tools.run("write_file", { path: "/tmp/x", content: "" }, ctx)).ok, false);
  assert.equal((await tools.run("codebase_search", { query: "a", path: "../.." }, ctx)).ok, false);
  assert.equal((await tools.run("bash", { command: "rm -rf /" }, ctx)).ok, false);
});

test("search finds a file by content", async () => {
  const ctx = { repoRoot: await tempRepo() };
  await fs.writeFile(path.join(ctx.repoRoot, "hello.ts"), "const greeting = 'hi';\n");
  const result = await new ToolRegistry().run("codebase_search", { query: "greeting" }, ctx);
  assert.match(result.output, /hello\.ts:1:/);
});

test("read_file returns long files in parts that can be read with offset", async () => {
  const ctx = { repoRoot: await tempRepo() };
  const lines = Array.from({ length: 500 }, (_, i) => `line ${i + 1} ${"x".repeat(40)}`);
  await fs.writeFile(path.join(ctx.repoRoot, "big.txt"), lines.join("\n"));
  const tools = new ToolRegistry();

  const first = await tools.run("read_file", { path: "big.txt" }, ctx);
  const next = Number(first.output.match(/offset=(\d+)/)?.[1]);
  assert.ok(next > 1 && !first.output.includes("cut"), "first part ends on a whole line with a next offset");

  const second = await tools.run("read_file", { path: "big.txt", offset: next }, ctx);
  assert.ok(second.output.startsWith(`${next}\tline ${next} `));

  const range = await tools.run("read_file", { path: "big.txt", offset: 10, limit: 2 }, ctx);
  assert.match(range.output, /^10\t.*\n11\t.*\n\n\[Showing lines 10-11 of 500/);
  assert.equal((await tools.run("read_file", { path: "big.txt", offset: 900 }, ctx)).ok, false);
});

test("Gemini client reports retries, and fails at once when the daily quota is used up", async (t) => {
  const ok = { candidates: [{ content: { role: "model", parts: [{ text: "hi" }] }, finishReason: "STOP" }] };
  const responses = [
    new Response('{"retryDelay": "0s"}', { status: 503 }),
    new Response(JSON.stringify(ok)),
    new Response('{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}', { status: 429 }),
  ];
  const fetchMock = t.mock.method(globalThis, "fetch", async () => responses.shift());
  const retries: string[] = [];
  const provider = new GeminiProvider("k", "m", (message) => retries.push(message));

  assert.equal((await provider.generateTurn("", [], [])).text, "hi");
  assert.match(retries[0], /503, retrying in \d+s \(attempt 2 of 6\)/);

  await assert.rejects(provider.generateTurn("", [], []), /daily quota/);
  assert.equal(fetchMock.mock.callCount(), 3, "daily quota is not retried");
});

test("parallel tool results go to Gemini as a single user message, with errors marked", () => {
  const history: Message[] = [
    { role: "user", content: "task" },
    { role: "assistant", content: "", toolCalls: [{ id: "1", name: "read_file", arguments: {} }, { id: "2", name: "bash", arguments: {} }] },
    { role: "tool", toolCallId: "1", toolName: "read_file", content: "a", isError: false },
    { role: "tool", toolCallId: "2", toolName: "bash", content: "b", isError: true },
    { role: "user", content: "please verify" },
    { role: "assistant", content: "" },
  ];
  const contents = toGeminiContents(history);
  assert.deepEqual(contents.map((c) => [c.role, c.parts.length]), [["user", 1], ["model", 2], ["user", 3]]);
  assert.deepEqual(contents[2].parts[0].functionResponse?.response, { output: "a" });
  assert.deepEqual(contents[2].parts[1].functionResponse?.response, { error: "b" });
});

test("full run through GeminiProvider against a fake Gemini API fixes a failing test", async (t) => {
  const repoRoot = await tempRepo();
  await fs.writeFile(path.join(repoRoot, "math.js"), "exports.add = (a, b) => a - b;\n");
  await fs.writeFile(path.join(repoRoot, "test.js"), "if (require('./math').add(2, 3) !== 5) process.exit(1);\n");

  const fc = (name: string, args: Record<string, unknown>) => ({ functionCall: { name, args }, thoughtSignature: "sig" });
  const script = [
    [fc("codebase_search", { query: "add" })],
    [fc("read_file", { path: "math.js" }), fc("bash", { command: "node test.js", verification: true })],
    [fc("write_file", { path: "math.js", content: "exports.add = (a, b) => a + b;\n" })],
    [fc("bash", { command: "node test.js", verification: true })],
    [{ text: "Fixed add()." }],
  ];

  t.mock.method(globalThis, "fetch", async (url: string, init: RequestInit) => {
    assert.equal((init.headers as Record<string, string>)["x-goog-api-key"], "test-key");
    assert.ok(!url.includes("key="), "API key must not be in the URL");

    // Gemini's rules: roles alternate, no empty contents, one function response per function call.
    const { contents } = JSON.parse(init.body as string) as { contents: ReturnType<typeof toGeminiContents> };
    contents.forEach((content, i) => {
      assert.ok(content.parts.length > 0);
      if (i > 0) assert.notEqual(content.role, contents[i - 1].role);
      const calls = content.parts.filter((p) => p.functionCall);
      if (calls.length === 0) return;
      assert.ok(calls.every((p) => p.thoughtSignature === "sig"));
      assert.equal(contents[i + 1].parts.filter((p) => p.functionResponse).length, calls.length);
    });

    const parts = script.shift();
    return new Response(JSON.stringify({ candidates: [{ content: { role: "model", parts }, finishReason: "STOP" }] }));
  });

  const provider = new GeminiProvider("test-key", "fake-model");
  const result = await new AgentLoop({ provider, repoRoot }).run("fix add");
  assert.equal(result.status, "completed");
  assert.equal(result.turnsUsed, 5);
  assert.match(await fs.readFile(path.join(repoRoot, "math.js"), "utf-8"), /a \+ b/);
});
