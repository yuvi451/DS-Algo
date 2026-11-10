# Deep dive: `src/tools/util.ts`

**What it does in one line:** it has two helpers the tools share. One keeps paths inside the repo. The other shortens long output.

The file has 3 parts:
1. Import (L1)
2. `resolveInRepo` (L3–14)
3. `truncate` (L16–23)

---

## 1. Import (L1)

```ts
import path from "node:path";
```
> **TS basics**
> - `node:path` is Node's built-in module for working with file paths. The `node:` prefix makes it clear that this is a built-in, not an npm package.
> - `import path from ...` is a **default import**. It gives you the whole module under the name `path`.

---

## 2. `resolveInRepo(repoRoot, relativePath)` (L7–14)

```ts
export function resolveInRepo(repoRoot: string, relativePath: string): string {
  const root = path.resolve(repoRoot);
  const resolved = path.resolve(root, relativePath);
  if (resolved !== root && !resolved.startsWith(root + path.sep)) {
    throw new Error(`Path "${relativePath}" is outside the repository (${root}).`);
  }
  return resolved;
}
```
> **TS:** `(a: string, b: string): string` gives the parameter types, and the type after `)` is the **return type**. `throw new Error(...)` stops the function and passes the error up to whoever called it.

Step by step:
1. `path.resolve(repoRoot)` turns the repo path into a clean absolute path.
2. `path.resolve(root, relativePath)` joins the two and handles `..`. If `relativePath` is **absolute** (like `/etc/passwd`), `path.resolve` ignores `root` and uses the absolute path.
3. The result is allowed if it is the root itself, or if it starts with `root + "/"`.
4. Otherwise it throws.

| Input (root = `/repo`) | Result |
|---|---|
| `src/a.ts` | `/repo/src/a.ts` ✅ |
| `.` | `/repo` ✅ |
| `../x` | `/x` ❌ throws |
| `/tmp/x` | `/tmp/x` ❌ throws |
| `../repo-evil/x` | `/repo-evil/x` ❌ throws |

**Why `root + path.sep` and not just `root`:** `/repo-evil` starts with `/repo`, so a plain `startsWith(root)` would let it through. Adding the separator (`/` on Mac and Linux) closes that gap.

**Limit (the comment says so too):** it doesn't follow **symlinks**. A symlink inside the repo that points outside would pass. It's a basic guard, not a sandbox.

Used by: `read.ts`, `write.ts`, `search.ts`.

---

## 3. `truncate(text, maxChars)` (L17–23)

```ts
if (text.length <= maxChars) return text;
const headChars = Math.floor(maxChars * 0.7);
const tailChars = maxChars - headChars;
const omitted = text.length - maxChars;
return `${text.slice(0, headChars)}\n\n[... ${omitted} characters cut ...]\n\n${text.slice(-tailChars)}`;
```
> **TS:**
> - `Math.floor` rounds down to a whole number.
> - `text.slice(0, n)` gives the first `n` characters. `text.slice(-n)` gives the **last** `n` characters, because negative numbers count from the end.
> - `` `...${x}...` `` is a template string, which inserts values into a string.

- Short text comes back unchanged.
- Long text keeps the **first 70%** and the **last 30%** of the budget, with a note in between saying how much was cut.
- The end is kept because errors and test summaries usually appear at the **end** of command output.

**Easy to miss:** the result is a bit **longer** than `maxChars`, because of the `[... N characters cut ...]` note. `maxChars` limits how much of the original text is kept, not the exact length of the result.

Used by: `read.ts` (8000 chars) and `bash.ts` (4000 chars for stdout and 4000 for stderr).
