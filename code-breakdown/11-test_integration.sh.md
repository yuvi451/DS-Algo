# 11 — `test/test_integration.sh`

**What it is:** an end-to-end test written in bash. It starts the real
server, runs the real client against it, and checks what gets printed.
Unlike the unit tests, this exercises everything together: sockets, the
event loop, framing, parsing, the store and the hashtable.

Run it with `make test-integration`, which builds AddressSanitizer versions
of both programs first. It takes about a minute.

---

## Lines 1–2: script setup

```bash
#!/usr/bin/env bash
set -euo pipefail
```

- **`#!/usr/bin/env bash`** (the "shebang"): tells the OS to run this file
  with bash, wherever bash is installed.
- **`set -e`**: stop the script as soon as any command fails.
- **`set -u`**: treat use of an undefined variable as an error (catches typos).
- **`set -o pipefail`**: in `a | b`, fail if `a` fails, not only if `b` fails.

Together they make a script fail loudly instead of carrying on after an error.

---

## Lines 4–11: find the binaries

```bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_BIN="$ROOT_DIR/build/server_asan"
CLIENT_BIN="$ROOT_DIR/build/client_asan"

if [[ ! -x "$SERVER_BIN" || ! -x "$CLIENT_BIN" ]]; then
    echo "build ASan binaries first (or run: make test-integration)" >&2
    exit 1
fi
```

- **Line 4:** work out the repo's root folder, no matter which directory the
  script is run from. `${BASH_SOURCE[0]}` is the script's own path;
  `dirname` strips the file name (`.../test`); `/..` goes up one level;
  `cd ... && pwd` turns that into an absolute path. `$(...)` runs a command
  and substitutes its output.
- **Lines 5–6:** use the **ASan** builds, so a memory bug inside the server
  crashes it during the test instead of going unnoticed.
- **Line 8:** `[[ -x file ]]` is true if the file exists and is executable.
  If either binary is missing, explain and stop. `>&2` sends the message to
  stderr.

---

## Lines 13–15: start the server in the background

```bash
"$SERVER_BIN" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true' EXIT
```

- **`&`** runs the server in the background, so the script continues.
- **`$!`** is the process ID of the last background command.
- **`trap '...' EXIT`** registers cleanup code that runs whenever the script
  exits: on success, on a failed check, or on Ctrl-C. It kills the server
  and waits for it to exit, so a failed test never leaves a server running
  and occupying port 1234. `2>/dev/null || true` hides errors if the server
  already exited.

---

## Lines 17–23: wait until the server is ready

```bash
# Wait for the server to accept connections.
for _ in $(seq 1 20); do
    if "$CLIENT_BIN" get __warmup__ >/dev/null 2>&1; then
        break
    fi
    sleep 0.1
done
```

The server needs a moment to start. Try a harmless `get` up to 20 times, 0.1
s apart (2 s max). As soon as one succeeds, the server is listening.

- `seq 1 20` prints 1 to 20; `_` is a throwaway loop variable.
- `>/dev/null 2>&1` discards both stdout and stderr.

> **CN refresher — why not just `sleep 1`?** Until the server has called
> `listen()`, a `connect()` to port 1234 fails with "Connection refused"
> (the kernel answers the SYN with a RST, because nobody is listening yet).
> Polling until a connection works is faster and more reliable than guessing
> a sleep time.

---

## Lines 25–28: helper

```bash
fail() {
    echo "FAIL: $1" >&2
    exit 1
}
```

Print a failure message and exit (which also triggers the cleanup trap).
`$1` is the function's first argument.

---

## Lines 30–46: behaviour checks

```bash
out="$("$CLIENT_BIN" get missing)"
[[ "$out" == "(nil)" ]] || fail "expected (nil) for missing key, got: $out"
```

Each check runs the client, captures what it printed in `out`, and compares.
`A || B` runs `B` only if `A` fails, so it reads as "this must be true, or
fail".

The sequence:

| Command | Expected | Checks |
|---|---|---|
| `get missing` | `(nil)` | Missing key → `Nx` |
| `set foo bar` | `OK` | Insert |
| `get foo` | `bar` | Read back |
| `del foo` | `OK` | Delete an existing key |
| `get foo` | `(nil)` | It's really gone |
| `nosuchcmd a b c` | `(error) …` | Unknown command → `Err` |

---

## Lines 48–57: the resize test

```bash
echo "Inserting 10000 keys to force a resize (this takes roughly a minute)..."
for i in $(seq 0 9999); do
    "$CLIENT_BIN" set "key$i" "val$i" >/dev/null
done

echo "Verifying a sample of keys survived rehashing..."
for i in 0 1 500 4999 5000 9998 9999; do
    out="$("$CLIENT_BIN" get "key$i")"
    [[ "$out" == "val$i" ]] || fail "expected val$i for key$i after rehash, got: $out"
done
```

10,000 inserts push the server's hashtable through 9 resizes (up to 2,048
buckets), several of them spread across many requests. Then spot-check keys
from the start, middle and end.

**Why it's slow:** each `set` starts a new client process (with ASan, which
is slow to start) and opens a new TCP connection. The server itself handles
each request in microseconds.

> **CN refresher — 10,000 connections in a row:** each client connects,
> sends one request, reads the reply and closes. Because the client closes
> first, each client port stays in **TIME_WAIT** for ~30 s. macOS has about
> 16,000 ephemeral ports (49152–65535), so 10,000 short connections fit. A
> test with 50,000 connections in under 30 s could run out of ports and
> start failing with `EADDRNOTAVAIL`. This is one reason real clients keep
> connections open and reuse them.

---

## Line 59

```bash
echo "All integration tests passed."
```

Reaching this line means every check passed. The `trap` then stops the server.

**A gap to know about:** the script kills the server with SIGTERM and
doesn't inspect its output. ASan errors during requests would crash the
server and fail the next check, but memory leaks (which ASan reports at
normal exit) are never seen.
