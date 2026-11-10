# Deep dive: `src/tools/search.ts`

**What it does in one line:** it goes through every file in the repo (or in one folder) and returns the file names and lines that match a keyword or regex. The search ignores case and has limits so it can't run away.

The file has 5 parts:
1. Imports and limits (L1–10)
2. `definition` (L13–27)
3. `execute`: setup, the `walk` function, formatting the results (L29–87)
4. `readLines` helper (L90–98)
5. `escapeRegExp` helper (L100–102)

---

## 1. Limits (L6–10)

```ts
const SKIPPED_DIRS = new Set(["node_modules", "dist", "build", "out", "coverage", "__pycache__"]);
const MAX_MATCHES = 50;
const MAX_FILE_NAME_MATCHES = 20;
const MAX_FILES = 5000;
const MAX_FILE_BYTES = 1_000_000;
```
> **TS basics**
> - `Set` is a collection of unique values. `set.has(x)` is a fast membership check.
> - `1_000_000`: the underscores are **numeric separators**, only there to make the number readable. The value is 1000000.

| Limit | Why |
|---|---|
| `SKIPPED_DIRS` | Generated or dependency folders, which are huge and not useful to search |
| `MAX_MATCHES` 50 | Stops collecting matching lines after 50 |
| `MAX_FILE_NAME_MATCHES` 20 | Only 20 file-name matches are **shown** |
| `MAX_FILES` 5000 | Stops after looking at 5000 files |
| `MAX_FILE_BYTES` 1 MB | Skips reading the contents of bigger files |

---

## 2. `definition` (L13–27)

The arguments are `query` (required), `path` (an optional folder to search in), and `regex` (true means `query` is a regular expression; by default it is a plain keyword). The description tells the model to **search first instead of guessing paths**.

---

## 3. `execute(args, ctx)` (L29–87)

**a) Read the inputs (L30–32)**
```ts
const query = String(args.query ?? "");
const folder = typeof args.path === "string" && args.path ? args.path : ".";
```
The folder defaults to `"."`, which is the repo root.

**b) Build the start folder and the pattern (L34–41)**
```ts
let startDir: string;
let pattern: RegExp;
try {
  startDir = resolveInRepo(ctx.repoRoot, folder);
  pattern = new RegExp(args.regex === true ? query : escapeRegExp(query), "i");
} catch (err) { return { ok: false, output: (err as Error).message }; }
```
> **TS:** The variables are declared with a type but **no value** (`let x: T;`), and set inside the `try`. TypeScript knows that every path that reaches the code after the `try` has assigned them. This is called **definite assignment analysis**.

- Two things can throw here: a path outside the repo, or an **invalid regex** the model wrote (like `"("`). Both become a readable error.
- When `regex` isn't `true`, the query is escaped so that characters like `.` or `(` are matched literally.
- The `"i"` flag makes the match ignore case. There is **no** `"g"` flag on purpose: a regex with `g` remembers where its last match was, which would make repeated `.test()` calls skip matches.

**c) Where results are stored, and the stop condition (L43–46)**
```ts
const nameMatches: string[] = [];
const lineMatches: string[] = [];
let filesSeen = 0;
const isFull = () => lineMatches.length >= MAX_MATCHES || filesSeen >= MAX_FILES;
```
> **TS:** `isFull` is an arrow function that reads the variables around it. This is a **closure**: every time it is called, it sees the current values.

**d) `walk(dir)`: go through folders recursively (L48–71)**
```ts
async function walk(dir: string): Promise<void> {
  const entries = await fs.readdir(dir, { withFileTypes: true }).catch(() => []);
```
> **TS:**
> - A function declared **inside** another function can use the outer function's variables (`pattern`, `lineMatches`, `ctx`, and so on).
> - `Promise<void>` means it is async and returns nothing useful.
> - `.catch(() => [])`: if a folder can't be read (for example, no permission), use an empty list instead of failing the whole search.

For each entry:
1. `if (isFull()) return;` stops as soon as a limit is reached.
2. It skips names that start with `.` (`.git`, `.env`, `.venv`). This avoids noise, and also keeps **secrets in `.env`** out of the results.
3. For a folder, it calls `walk` on it (**recursion**) unless the folder is in `SKIPPED_DIRS`, then `continue`s.
4. It skips anything that isn't a regular file (symlinks, sockets, and so on).
5. For a file:
   - `filesSeen++`
   - `relPath = path.relative(ctx.repoRoot, fullPath)`, so results are shown relative to the **repo root**
   - if the **file name** matches, it is added to `nameMatches`
   - it reads the lines, and each matching line is added as `path:lineNo: text`. The text is trimmed and cut to 200 characters, and the loop stops once there are 50 matches.

**e) Start the walk (L73)**
`await walk(startDir);`

**f) Format the results (L75–86)**
- Nothing found: `No matches for "x" in ".".` with `ok: true`. Finding nothing is a valid answer, not an error.
- Otherwise it builds up to two sections:
  - `Matching file names:`, showing the first 20
  - `Matching lines (N):`, where N becomes `50+, list cut short` if the limit was hit
- The sections are joined with a blank line between them.

---

## 4. `readLines(file)` (L91–98)

```ts
try {
  if ((await fs.stat(file)).size > MAX_FILE_BYTES) return [];
  return (await fs.readFile(file, "utf-8")).split("\n");
} catch { return []; }
```
> **TS:** `catch {` with no `(err)` is **optional catch binding**. You write it that way when you don't need the error.

A file that is too big or can't be read gives back no lines, so one bad file doesn't stop the search. A big file's **name** can still match, because name matching happens before its contents are read.

---

## 5. `escapeRegExp(text)` (L100–102)

```ts
return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
```
> **TS/JS:** `/.../g` is a regex literal, and `g` here means "replace every match". In the replacement string, `$&` means "the text that matched". So each special character gets a `\` in front of it.

Example: `a.b(` becomes `a\.b\(`, which matches the literal text `a.b(`.

---

## Easy to miss
- Once 50 matching lines have been found, the walk stops **entirely**. More matching file names may be missed after that point.
- Name matches are collected for every file seen, but only 20 are **shown**.
- If the model writes a very slow regex (catastrophic backtracking), it could hang the search. No timeout guards against that.
