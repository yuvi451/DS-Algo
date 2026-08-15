#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_BIN="$ROOT_DIR/build/server_asan"
CLIENT_BIN="$ROOT_DIR/build/client_asan"

if [[ ! -x "$SERVER_BIN" || ! -x "$CLIENT_BIN" ]]; then
    echo "build ASan binaries first: make $SERVER_BIN $CLIENT_BIN" >&2
    exit 1
fi

"$SERVER_BIN" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 20); do
    if "$CLIENT_BIN" get __warmup__ >/dev/null 2>&1; then
        break
    fi
    sleep 0.1
done

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

out="$("$CLIENT_BIN" get missing)"
[[ "$out" == "(nil)" ]] || fail "expected (nil) for missing key, got: $out"

out="$("$CLIENT_BIN" set foo bar)"
[[ "$out" == "OK" ]] || fail "expected OK for set, got: $out"

out="$("$CLIENT_BIN" get foo)"
[[ "$out" == "bar" ]] || fail "expected bar for get foo, got: $out"

out="$("$CLIENT_BIN" del foo)"
[[ "$out" == "OK" ]] || fail "expected OK for del, got: $out"

out="$("$CLIENT_BIN" get foo)"
[[ "$out" == "(nil)" ]] || fail "expected (nil) after del, got: $out"

out="$("$CLIENT_BIN" nosuchcmd a b c)"
[[ "$out" == "(error) unknown command or wrong number of arguments" ]] || fail "expected error for unknown command, got: $out"

echo "Inserting 10000 keys to force a resize (this takes roughly a minute)..."
for i in $(seq 0 9999); do
    "$CLIENT_BIN" set "key$i" "val$i" >/dev/null
done

echo "Verifying a sample of keys survived rehashing..."
for i in 0 1 500 4999 5000 9998 9999; do
    out="$("$CLIENT_BIN" get "key$i")"
    [[ "$out" == "val$i" ]] || fail "expected val$i for key$i after rehash, got: $out"
done

echo "All integration tests passed."
