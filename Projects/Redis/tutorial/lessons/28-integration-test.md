---
title: An end-to-end test in bash
module: Ship it
time: 35 min
---

:::goal
Unit tests check pieces. An **integration test** checks the real programs
working together: start the server, run the real client, compare outputs,
and insert 10,000 keys to make the hashtable grow several times. Write
`test/test_integration.sh`.
:::

## The script

@include ../test/test_integration.sh

## Line by line

| Code | Meaning |
|---|---|
| `#!/usr/bin/env bash` | "Run this file with bash." Called a *shebang*. |
| `set -euo pipefail` | Bash **strict mode**: `-e` stop on any failing command, `-u` error on unset variables, `-o pipefail` a pipeline fails if any part fails. Without it, scripts silently keep going after errors. |
| `ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"` | The project root: the folder above this script's folder. So the test works no matter which directory you run it from. |
| `[[ ! -x "$SERVER_BIN" … ]]` | "If the server binary doesn't exist or isn't executable": a friendly error instead of a confusing one. |
| `"$SERVER_BIN" &` | Start the server **in the background** (`&`), so the script continues. |
| `SERVER_PID=$!` | `$!` = process ID of the last background program. We need it to stop the server. |
| `trap '…' EXIT` | "When this script exits, **for any reason** (success, failure, Ctrl+C), run this cleanup": kill the server and wait for it. No orphaned servers left on port 1234. |
| warm-up loop | Retry a harmless `get` up to 20 times, 0.1 s apart, until the server answers. Starting takes a moment. |
| `out="$("$CLIENT_BIN" get missing)"` | Run the client and **capture** what it printed into `out`. |
| `[[ "$out" == "(nil)" ]] \|\| fail "…"` | If the output isn't what we expect, call `fail`, which prints and exits 1. |
| `for i in $(seq 0 9999)` | 10,000 `set`s. With load factor 8 and doubling, that takes the table from 4 up to 2048 buckets. |

:::why Why does it take a while (around 30 seconds)?
Each `set` starts a **new client process** with a new TCP connection.
10,000 process launches add up. (Each closed
connection also leaves a socket in `TIME_WAIT` for a while. macOS has about
16,000 ephemeral ports, so 10,000 connections fit comfortably.)
:::

:::task Write and run the integration test
1. Create `test/test_integration.sh` with the content above.
2. Make it executable: `chmod +x` adds the "may be run as a program" permission.
3. Run the full test suite:

```bash
$ chmod +x test/test_integration.sh
$ make test
```
:::

```output
…unit test output…
All hashtable tests passed.
…
All protocol tests passed.
test/test_integration.sh
listening on 127.0.0.1:1234
Inserting 10000 keys to force a resize (this takes a little while)...
Verifying a sample of keys survived rehashing...
All integration tests passed.
```

:::hint Hint: `bind() failed: Address already in use`
Your own `build/server` is still running from an earlier lesson. Stop it
(Ctrl + C in its terminal) and run `make test` again.
:::

:::hint Hint: `Permission denied`
You skipped `chmod +x test/test_integration.sh`.
:::

:::recap
- Integration test = real binaries, real sockets, real outputs.
- `set -euo pipefail` for safety, `&` + `$!` to run the server in the background, `trap … EXIT` to always clean up.
- `make test` now runs every test.
:::
