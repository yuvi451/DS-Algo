# Deep dive: `src/tools/write.ts`

**What it does in one line:** it creates a file or overwrites it completely, creating any missing folders, and reports whether the file was created or overwritten.

The file has 2 parts:
1. `definition` (L7–20)
2. `execute` (L22–38)

---

## 1. `definition` (L7–20)

The arguments are `path` and `content`, and both are required.

The description says it clearly: **this replaces the whole file**. There is no "patch" or "edit lines" tool. So the model must send the **complete** file every time, which is why the system prompt and `read_file` make it read the whole file first.

---

## 2. `execute(args, ctx)` (L22–38)

**a) Inputs (L23–25)**
```ts
const relPath = String(args.path ?? "");
const content = typeof args.content === "string" ? args.content : "";
if (!relPath) return { ok: false, output: "`path` must be a non-empty string." };
```
If `content` isn't a string, it falls back to `""`. In practice the registry has already rejected a missing or non-string `content`, so this is a second layer of defence.

**b) Resolve the path safely (L28)**
`resolveInRepo` throws for paths outside the repo, such as `../x` or `/tmp/x`. The throw lands in the `catch`.

**c) Check whether the file already existed (L29)**
```ts
const existed = await fs.access(absPath).then(() => true, () => false);
```
> **TS basics:**
> - `fs.access(path)` **resolves** if the path exists and **rejects** if it doesn't.
> - `.then(onSuccess, onFailure)` takes two handlers. Here it turns "resolves or rejects" into `true` or `false`, so no `try/catch` is needed.

This is only used for the message at the end ("Created" or "Overwrote").

**d) Create folders, then write (L30–31)**
```ts
await fs.mkdir(path.dirname(absPath), { recursive: true });
await fs.writeFile(absPath, content, "utf-8");
```
- `path.dirname("src/a/b.ts")` gives `"src/a"`, the folder part.
- `recursive: true` creates every missing parent folder, and it **doesn't fail** if the folder already exists.
- `writeFile` creates the file or replaces all of its contents.

**e) Report (L33–34)**
```ts
const lines = content.split("\n").length;
return { ok: true, output: `${existed ? "Overwrote" : "Created"} "${relPath}" (${lines} lines).` };
```
For example: `Created "src/a.ts" (12 lines).`

**f) Errors (L35–37)**
Any failure (outside the repo, permission denied, the path is a folder, and so on) becomes `Could not write "x": <reason>` with `ok: false`.

---

## How the loop uses it
In `loop.ts`, a `write_file` result with `ok: true` sets `hasUnverifiedEdits = true`. From then on, the run can't end as `completed` until a verification passes.

## Easy to miss
- Content ending in `\n` counts one extra line (`"a\n"` reports 2 lines).
- The write is **not atomic**. If the process dies in the middle, the file can be left half-written.
- There is no backup or undo. Git is your safety net.
