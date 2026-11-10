# Deep dive: `src/tools/read.ts`

**What it does in one line:** it reads a file and returns it with line numbers, in parts of about 8000 characters. If the path is a folder, it lists what's inside.

The file has 3 parts:
1. Imports and a constant (L1–5)
2. `definition`, what the model sees (L8–23)
3. `execute`, what actually happens (L25–65)

---

## 1. Imports and constant (L1–5)

```ts
import fs from "node:fs/promises";
const MAX_CHARS = 8000;
```
> **TS basics:** `node:fs/promises` is Node's file-system module where every function returns a **Promise**, so you `await` it. The older `node:fs` uses callbacks or blocking calls.

`MAX_CHARS` is the most text returned in one call. It stops a big file from filling the model's context.

---

## 2. The tool object and its `definition` (L7–23)

```ts
export const readTool: Tool = {
  definition: { name: "read_file", description: "...", parameters: { ... required: ["path"] } },
  async execute(args, ctx) { ... },
};
```
> **TS:**
> - The tool is a plain **object literal** with the type `Tool`, not a class. TypeScript checks that it has `definition` and `execute` with the right types.
> - `async execute(args, ctx) {...}` is **method shorthand**. Because the object is typed as `Tool`, TypeScript already knows the types of `args` and `ctx`, so they don't need writing out. This is called **contextual typing**.

The arguments:

| Arg | Type | Meaning |
|---|---|---|
| `path` | string, required | File or folder, relative to the repo root |
| `offset` | number | The first line to return (1-based). Default 1 |
| `limit` | number | The most lines to return. Default: as many as fit |

---

## 3. `execute(args, ctx)` (L25–65)

**a) Check the path (L26–27)**
```ts
const relPath = String(args.path ?? "");
if (!relPath) return { ok: false, output: "`path` must be a non-empty string." };
```
`args.path` is `unknown`. `?? ""` replaces `null` or `undefined` with an empty string, and `String(...)` turns the value into a string.

**b) Make it absolute and safe (L30)**
`resolveInRepo` throws if the path points outside the repo. The `catch` at the bottom turns that into `ok: false`.

**c) If it's a folder, list it (L32–36)**
```ts
if ((await fs.stat(absPath)).isDirectory()) {
  const entries = await fs.readdir(absPath, { withFileTypes: true });
  const listing = entries.map((e) => `${e.isDirectory() ? "d" : "f"} ${e.name}`).sort().join("\n");
```
- `fs.stat` gets information about the path. `(await x).method()`: the brackets make sure the value is awaited **before** the method is called.
- `withFileTypes: true` makes `readdir` return objects that have `.isDirectory()`, instead of plain names.
- The output has one line per entry, such as `d src` or `f package.json`, sorted.

**d) Read the file and work out the range (L38–44)**
```ts
const lines = (await fs.readFile(absPath, "utf-8")).split("\n");
const start = typeof args.offset === "number" ? Math.max(1, Math.floor(args.offset)) : 1;
if (start > lines.length) return { ok: false, output: `offset ${start} is past the end ...` };
const limit = typeof args.limit === "number" && args.limit >= 1 ? Math.floor(args.limit) : lines.length;
const end = Math.min(lines.length, start + limit - 1);
```
> **TS:** `typeof args.offset === "number"` is a **type guard**. Inside the true branch, TypeScript treats `args.offset` as a `number`, not `unknown`.

- `start`: a whole number of at least 1, defaulting to 1.
- `limit`: a whole number of at least 1, defaulting to "all lines".
- `end`: the last line wanted, never past the end of the file.

**e) Add lines until the budget is full (L47–54)**
```ts
let output = "";
let last = start - 1;
for (let n = start; n <= end; n++) {
  const line = `${n}\t${lines[n - 1]}\n`;
  if (output && output.length + line.length > MAX_CHARS) break;
  output += line;
  last = n;
}
```
- Each line is formatted as `number<TAB>text`. `lines[n - 1]` is there because arrays start at 0 but line numbers start at 1.
- It stops at a **whole line** once the next one wouldn't fit. The model never sees half a line, and it knows exactly where to continue.
- `if (output && ...)`: the **first** line is always added, even if it's too long on its own. Otherwise one huge line would give empty output forever.
- `last` remembers the last line that was added.

**f) Cut a single huge line, then add the "read more" note (L56–60)**
```ts
output = truncate(output, MAX_CHARS);
if (last < lines.length) output += `\n[Showing lines ${start}-${last} of ${lines.length}. Use offset=${last + 1} to read more.]`;
```
`truncate` only does anything when that first line was too big (for example minified JS). The footer tells the model which `offset` to use next. The system prompt tells the model to keep reading until it has the whole file, because `write_file` needs the complete content.

**g) Errors (L61–64)**
```ts
const notFound = (err as NodeJS.ErrnoException).code === "ENOENT";
return { ok: false, output: notFound ? `File not found: ${relPath}` : (err as Error).message };
```
> **TS:** `NodeJS.ErrnoException` is Node's error type with a `.code` field. `ENOENT` means "no such file or directory". The `as` cast is needed because `err` is `unknown`.

---

## Easy to miss
- A file ending in `\n` splits into one extra empty last "line", so the line count can be one higher than an editor shows.
- The footer shows when there are more lines after `last`, even if you set `limit` yourself. That is intended, because it tells you the file continues.
- Binary files are read as UTF-8 text anyway, so they come back as unreadable characters.
