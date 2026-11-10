# Deep dive: `src/tools/types.ts`

**What it does in one line:** it defines the shapes that every tool uses: what the model is told about a tool, what the tool gets when it runs, and what it gives back.

There is no runtime code here, only types. After compiling, this file is basically empty.

The file has 5 interfaces:
1. `JsonSchema` (L1–8)
2. `ToolDefinition` (L10–15)
3. `ToolContext` (L17–20)
4. `ToolResult` (L22–26)
5. `Tool` (L28–31)

---

## 1. `JsonSchema` (L1–8)

```ts
export interface JsonSchema {
  type: string;
  description?: string;
  properties?: Record<string, JsonSchema>;
  items?: JsonSchema;
  required?: string[];
  enum?: string[];
}
```
> **TS basics**
> - `interface` describes the shape of an object. `export` lets other files import it.
> - `?` means the property is optional.
> - `Record<string, JsonSchema>` is an object whose keys are strings and whose values are `JsonSchema`.
> - The type refers to itself (`properties` and `items` are `JsonSchema` too). This is a **recursive type**, which is how nested objects and arrays are described.

This is a small subset of **JSON Schema**, the standard format for describing JSON data. Each tool uses it to describe its arguments, for example "`path` is a string and it is required".

| Field | Meaning |
|---|---|
| `type` | `"object"`, `"string"`, `"number"`, `"boolean"`, `"array"` |
| `description` | Text that tells the model what the field is for |
| `properties` | The fields inside an object, each with its own schema |
| `items` | The schema of each element, when `type` is `"array"` |
| `required` | Names of the fields that must be present |
| `enum` | The only values allowed |

---

## 2. `ToolDefinition` (L10–15)

```ts
export interface ToolDefinition { name: string; description: string; parameters: JsonSchema; }
```
This is **what the model sees** about a tool: its name, what it does, and its arguments. It gets sent to the model every turn. `gemini.ts` converts it into Gemini's format.

---

## 3. `ToolContext` (L17–20)

```ts
export interface ToolContext { repoRoot: string; }
```
This is extra information the **agent** passes to a tool when running it. The model never sees it. For now it only holds the repository path, so tools know where "the repo" is.

Why it's separate from the arguments: the model decides the arguments, but it must **not** get to decide where the repo is.

---

## 4. `ToolResult` (L22–26)

```ts
export interface ToolResult { ok: boolean; output: string; }
```
Every tool returns this. `ok` says whether the tool succeeded. `output` is the text the model reads next. The loop uses `ok` to set `isError` and to decide whether a verification passed.

---

## 5. `Tool` (L28–31)

```ts
export interface Tool {
  definition: ToolDefinition;
  execute(args: Record<string, unknown>, ctx: ToolContext): Promise<ToolResult>;
}
```
> **TS:**
> - `execute(...)` inside an interface is a **method signature**. Any object that claims to be a `Tool` must have this method with these parameter and return types.
> - `Record<string, unknown>`: the arguments come from the model as raw JSON, so their types are not known yet. `unknown` forces each tool to check a value before using it.
> - `Promise<ToolResult>` means `execute` is async and eventually gives back a `ToolResult`.

A tool is made of two parts: its **description** (`definition`) and its **behaviour** (`execute`). The four tools (`read`, `write`, `search`, `bash`) are each one object of this shape.

---

## How it connects

```
ToolDefinition ──→ sent to the model (so it knows which tools exist)
model replies with a tool call {name, arguments}
registry finds the Tool by name → tool.execute(arguments, {repoRoot}) → ToolResult
ToolResult.output ──→ sent back to the model
```
