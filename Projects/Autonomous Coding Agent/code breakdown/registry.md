# Deep dive: `src/tools/registry.ts`

**What it does in one line:** it holds all the tools, gives the model their descriptions, and runs a tool by name. It checks the arguments first, and it **never throws**.

The file has 4 parts:
1. Imports (L1–5)
2. `ToolRegistry` class: constructor and `definitions` (L7–16)
3. `run()` (L18–38)
4. `checkArgs()` (L41–53)

---

## 1. Imports (L1–5)

```ts
import type { JsonSchema, Tool, ToolContext, ToolDefinition, ToolResult } from "./types.js";
import { searchTool } from "./search.js";
...
```
It imports the types (types only) and the four tool objects (real values).

---

## 2. Class, constructor, `definitions` (L7–16)

```ts
private readonly tools: Map<string, Tool>;

constructor(tools: Tool[] = [searchTool, readTool, writeTool, bashTool]) {
  this.tools = new Map(tools.map((tool) => [tool.definition.name, tool]));
}
```
> **TS basics**
> - `Map<string, Tool>` is a built-in key → value store. Here the key is the tool's name, and the value is the tool. `map.get(key)` looks one up.
> - `tools: Tool[] = [...]` is a **default parameter**. If you call `new ToolRegistry()` with nothing, it uses all four tools. The tests rely on this.
> - `array.map(fn)` makes a new array by running `fn` on each element. Here each tool becomes a `[name, tool]` pair, and `new Map(pairs)` builds the map from those pairs.

```ts
get definitions(): ToolDefinition[] {
  return [...this.tools.values()].map((tool) => tool.definition);
}
```
> **TS:**
> - `get` defines a **getter**. You read it like a property (`registry.definitions`), without `()`, but it runs code each time.
> - `this.tools.values()` returns an **iterator**, not an array. `[...iterator]` (spread) turns it into an array so that `.map` can be used.

It returns the list of tool descriptions that the loop sends to the model every turn.

---

## 3. `run(name, args, ctx)` (L19–38)

Three checks, then the tool runs. **Every path returns a `ToolResult`, and nothing throws.** Errors become `{ ok: false }` so the model can read them and fix its mistake.

**a) Unknown tool (L20–23)**
```ts
const tool = this.tools.get(name);
if (!tool) return { ok: false, output: `Unknown tool "${name}". Available tools: ...` };
```
`map.get` returns `undefined` if the name isn't there. The error lists the real tool names so the model can correct itself.

> **TS:** After `if (!tool) return ...`, TypeScript knows `tool` is not `undefined` below that point. This is called **narrowing**.

**b) Bad arguments (L25–31)**
```ts
const problems = checkArgs(tool.definition.parameters, args);
if (problems.length > 0) return { ok: false, output: `Invalid arguments ...\n- ${problems.join("\n- ")}\nReceived: ${JSON.stringify(args)}` };
```
It lists every problem at once, and echoes back what was received. `JSON.stringify` turns an object into a JSON string.

**c) Run it (L33–37)**
```ts
try { return await tool.execute(args, ctx); }
catch (err) { return { ok: false, output: `Tool "${name}" failed: ${(err as Error).message}` }; }
```
> **TS:** `return await` inside `try` matters. With only `return promise`, a rejection would happen **after** the function had left the `try`, and the `catch` would miss it. `await` makes the error land inside the `try`.

---

## 4. `checkArgs(schema, args)` (L42–53)

This is a small, top-level-only validator. It returns a list of problems, and an empty list means the arguments are fine.

```ts
for (const key of schema.required ?? []) {
  if (args[key] == null) problems.push(`"${key}" is required`);
}
```
> **TS:**
> - `schema.required ?? []` uses an empty list if there is no `required` field, so the loop simply doesn't run.
> - `== null` (two `=`) is true for **both** `null` and `undefined`. It's the one common case where `==` is used on purpose.

```ts
for (const [key, value] of Object.entries(args)) {
  const expected = schema.properties?.[key]?.type;
  const actual = Array.isArray(value) ? "array" : typeof value;
  if (expected && value != null && actual !== expected) problems.push(`"${key}" must be a ${expected}, got ${actual}`);
}
```
> **TS:**
> - `Object.entries(obj)` gives `[key, value]` pairs. `const [key, value]` is **array destructuring**.
> - `?.` is **optional chaining**: if the left side is `null` or `undefined`, the whole expression becomes `undefined` instead of crashing. `?.[key]` is the same thing for bracket access.
> - `typeof value` gives `"string"`, `"number"`, `"boolean"`, `"object"`, and so on. Arrays report `"object"`, so `Array.isArray` is needed to call them `"array"`.

It checks each argument the model sent:
- If the schema doesn't know the key, `expected` is `undefined` and the key is skipped. **Extra keys are allowed.**
- A `null` or `undefined` value is skipped, because the required check already handles missing values.
- If the types don't match, it records a problem, for example `"path" must be a string, got number`.

---

## Easy to miss
- It only checks **top-level** fields. Nested objects, `enum` values, and array items are not checked.
- `typeof NaN === "number"`, so `NaN` passes as a number.
- The tools still check their own inputs (for example `String(args.path ?? "")`), as a second layer of defence.
