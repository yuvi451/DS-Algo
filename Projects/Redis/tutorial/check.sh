#!/usr/bin/env bash
# Compiles and runs every code snapshot the tutorial shows, so no lesson's
# "solution" can drift into something that doesn't build.
# usage: tutorial/check.sh   (from anywhere; stops any server on port 1234 first)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE="$ROOT/tutorial/code"
WORK="$(mktemp -d)"
trap 'kill $(jobs -p) 2>/dev/null || true; rm -rf "$WORK"' EXIT

CXX="c++ -std=c++17 -Wall -Werror"  # same flags as the Makefile, warnings fail

# Lay out a project dir: final repo files, then a stage's files on top.
project() {
    rm -rf "$WORK/p" && mkdir -p "$WORK/p"
    cp -R "$ROOT/src" "$ROOT/test" "$ROOT/bench" "$WORK/p/"
    mkdir -p "$WORK/p/scratch" "$WORK/p/build"
    for stage in "$@"; do
        cp -R "$CODE/$stage/." "$WORK/p/"
    done
    cd "$WORK/p"
}

expect() {  # expect <name> <expected> <actual>
    if [[ "$2" != "$3" ]]; then
        printf 'FAIL %s\n--- expected\n%s\n--- got\n%s\n' "$1" "$2" "$3" >&2
        exit 1
    fi
    echo "ok   $1"
}

start_server() {
    "$1" >"$WORK/server.log" 2>&1 &
    SERVER_PID=$!
    sleep 0.4
}
stop_server() { kill "$SERVER_PID"; wait "$SERVER_PID" 2>/dev/null || true; }

# --- a: C++ warm-ups
project
for p in hello bytes pointers classes; do
    $CXX "$CODE/a-basics/$p.cpp" -o "build/$p"
    echo "ok   a-basics/$p builds"
done
$CXX "$CODE/a-basics/main.cpp" "$CODE/a-basics/greet.cpp" -o build/greet
expect "a-basics/greet" "hello, redis!" "$(build/greet)"
expect "a-basics/bytes" "bytes in memory: 4 3 2 1" "$(build/bytes | sed -n 3p)"

# --- b: file descriptors
$CXX "$CODE/b-net/fds.cpp" -o build/fds
(cd build && ./fds >/dev/null 2>&1)
echo "ok   b-net/fds runs"

# --- c: blocking sockets
for p in listen_server hello_server hello_client stream_client sleepy_server; do
    $CXX "$CODE/c-sockets/$p.cpp" -o "build/$p"
done
start_server build/hello_server
expect "c-sockets/hello" "server says: world" "$(build/hello_client)"
stop_server
start_server build/sleepy_server
expect "c-sockets/stream demo" "server says: world" "$(build/stream_client)"
stop_server

# --- d: protocol stages 1-4, then the final files
for s in 1 2 3 4; do
    project "d-protocol/s$s"
    $CXX -o build/test_protocol test/test_protocol.cpp src/protocol.cpp
    build/test_protocol >/dev/null
    echo "ok   d-protocol/s$s tests pass"
done

# --- e: server stages (on top of the final protocol)
project
$CXX -o build/client src/client.cpp src/protocol.cpp
for s in 1 2 3 4; do
    project "e-server/s$s"
    $CXX -o build/server src/server.cpp src/protocol.cpp
    $CXX -o build/client src/client.cpp src/protocol.cpp
    start_server build/server
    case $s in
        1) nc -z 127.0.0.1 1234 >/dev/null 2>&1; sleep 0.2
           expect "e-server/s1" "accepted a connection on fd 4" "$(sed -n 2p "$WORK/server.log")" ;;
        2) (printf 'hello\n'; sleep 0.2) | nc 127.0.0.1 1234; sleep 0.2
           expect "e-server/s2" "fd 4: read 6 bytes, 6 bytes buffered so far" "$(sed -n 3p "$WORK/server.log")" ;;
        3) expect "e-server/s3" "(error) unknown command or wrong number of arguments" "$(build/client get foo)" ;;
        4) build/client set foo bar >/dev/null
           expect "e-server/s4" "bar" "$(build/client get foo)"
           $CXX -o build/pipeline "$CODE/e-server/pipeline.cpp" src/protocol.cpp -I src
           expect "e-server/pipeline" 'reply 2: status=0 data="c++"' "$(build/pipeline | sed -n 3p)" ;;
    esac
    stop_server
done

# --- f: hashtable stages
project "f-hashtable/s1"
$CXX -o build/fnv "$CODE/f-hashtable/fnv.cpp" src/hashtable.cpp -I src
build/fnv >/dev/null
echo "ok   f-hashtable/s1 fnv"
project "f-hashtable/s2"
$CXX -o build/test_hashtable test/test_hashtable.cpp src/hashtable.cpp
build/test_hashtable >/dev/null
echo "ok   f-hashtable/s2 tests pass"

# --- final: the real repo
cd "$ROOT"
make -s all bench build/test_hashtable build/test_protocol >/dev/null
build/test_hashtable >/dev/null && build/test_protocol >/dev/null
echo "ok   final repo builds, unit tests pass"
echo "All tutorial snapshots verified."
