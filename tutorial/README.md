# Build MicroRedis from Scratch: the course

A step-by-step, beginner-friendly course that rebuilds this repository's
server from zero. It assumes only DSA-level C++.

**Open it:** double-click `tutorial/index.html` (no server or install needed).
Progress is saved in your browser.

| Path | What it is |
|---|---|
| `lessons/NN-id.md` | Lesson sources (Markdown + `:::task`/`:::hint`/`:::solution`/`:::quiz`/… boxes) |
| `code/` | Every intermediate code snapshot the lessons show, organised by part and stage |
| `build.py` | Bundles the lessons into `assets/content.js`. `@include` lines pull code from `code/` and from the real `src/`, `test/`, `bench/` files |
| `check.sh` | Compiles and runs every snapshot (with `-Werror`) and the final repo, comparing outputs |

After editing a lesson or any source file:

```sh
python3 tutorial/build.py   # regenerate assets/content.js
tutorial/check.sh           # verify every snapshot still builds and behaves (stop any server on :1234 first)
```

The final-stage solutions come straight from `src/`, so the course always
matches the current implementation.
