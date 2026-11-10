import path from "node:path";

/**
 * Resolves a path against the repo root and throws if it points outside the repo (via `..` or an
 * absolute path). This is a basic guard, not a sandbox: it does not follow symlinks.
 */
export function resolveInRepo(repoRoot: string, relativePath: string): string {
  const root = path.resolve(repoRoot);
  const resolved = path.resolve(root, relativePath);
  if (resolved !== root && !resolved.startsWith(root + path.sep)) {
    throw new Error(`Path "${relativePath}" is outside the repository (${root}).`);
  }
  return resolved;
}

/** Keeps the start and end of long output (where errors usually show up) and drops the middle. */
export function truncate(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  const headChars = Math.floor(maxChars * 0.7);
  const tailChars = maxChars - headChars;
  const omitted = text.length - maxChars;
  return `${text.slice(0, headChars)}\n\n[... ${omitted} characters cut ...]\n\n${text.slice(-tailChars)}`;
}
