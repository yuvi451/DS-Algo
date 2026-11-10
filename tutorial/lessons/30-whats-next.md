---
title: You built Redis! Review and what's next
module: Ship it
time: 30 min
---

:::goal
Step back and see the whole system at once, check it against the final
project, review its known limitations honestly, and pick your next challenge.
:::

## The whole system on one page

```text
  build/client set foo bar                          build/server
 ┌──────────────────────────┐                 ┌─────────────────────────────────────┐
 │ client.cpp               │                 │ server.cpp                          │
 │  argv → encodeRequest    │   TCP over      │  poll() event loop (one thread)     │
 │  writeFrame ─────────────────► 127.0.0.1 ──────► handleRead → incoming buffer    │
 │                          │   port 1234     │     handleRequests (loop):          │
 │                          │                 │       tryParseFrame → parseRequest  │
 │                          │                 │       runCommand → db (HashMap)     │
 │                          │                 │                                     │
 │  readFrame ◄──────────────────────────────────── handleWrite ← outgoing buffer   │
 │  parseResponse → print   │                 │                                     │
 └──────────────────────────┘                 └─────────────────────────────────────┘
        uses protocol.cpp                         uses protocol.cpp + hashtable.cpp
```

The life of one `set foo bar`:

1. **client**: `argv` → `{"set","foo","bar"}` → `encodeRequest` → `connectToServer` → `writeFrame` (29 bytes).
2. **kernel**: TCP carries the bytes over loopback into the server socket's receive buffer.
3. **server**: `poll()` reports `POLLIN` on that fd → `handleRead` appends to `incoming`.
4. `handleRequests`: `tryParseFrame` = `FRAME_COMPLETE` → `parseRequest` → `runCommand` → `db.set` → `hashString` (FNV-1a) → `findNode` misses → `new Node` → `addNode` (and maybe move 128 nodes to the bigger table).
5. `encodeResponse(RES_OK)` → `makeFrame` → added to `outgoing` → `wantWrite = true`.
6. Next `poll()` round includes `POLLOUT` → `handleWrite` → `write()` 5 bytes → `wantWrite = false`.
7. **client**: `readFrame` → `parseResponse` → prints `OK` → `close()`. The server reads EOF → `wantClose` → `close(fd)` and `delete conn`.

## Check your work against the final project

Your files should now match the final project exactly. Compare any file with
the [final code appendix](#final-code), or run the whole suite:

```bash
$ make clean && make && make test
```

## Known limitations (on purpose)

| Limitation | Why it exists | How you'd fix it |
|---|---|---|
| `erase(0, n)` on the `incoming`/`outgoing` strings is O(length) per call | Simplicity | Keep a read offset and compact only occasionally, as the book's chapter 6 suggests |
| `set k ""` then `get k` prints `OK`, not an empty value | Data is omitted from the response when empty | Always send the length for `RES_OK` replies to `get`, or add a separate "string" type tag |
| No backpressure: a client that never reads its replies makes `outgoing` grow forever | Simplicity | Stop reading from (or disconnect) a client whose `outgoing` exceeds a limit |
| Replies still queued when a client closes are dropped | We close on `POLLHUP` immediately | Flush `outgoing` before closing when possible |
| `poll()` passes every fd on every call | Simplest portable API | Use `epoll` (Linux) or `kqueue` (macOS) |
| Not real RESP, so `redis-cli` can't connect | Binary protocol is simpler to teach | Implement RESP (a CodeCrafters-style challenge!) |

## Where to go next

**Book chapters 9+** (*Build Your Own Redis*, build-your-own.org) continue
from exactly where this project stops:

- **Serialization** of more data types (integers, arrays, nil) in responses
- **Sorted sets** with an AVL tree + the hashtable
- **Timers**: idle-connection timeouts using `poll()`'s timeout argument
- **TTL** (key expiry) with a heap
- **A thread pool** for slow deletions

**CodeCrafters' Redis challenge** goes the other way: real RESP, `ECHO`,
`PING`, expiry, persistence (RDB files), replication. With the event loop you
built here, you already know the hardest part.

**Small exercises** to try right now:

1. Add an `exists k` command. It only touches `runCommand`.
2. Fix the O(n) `erase(0, n)` with a read offset, then rerun the benchmark.
3. Add a `dbsize` command that returns `to_string(db.size())`.
4. Make `handleRead` call `handleWrite` immediately when it produces output
   (the book's "optimistic write"), and measure the effect with `loadtest`.

:::recap
You learned bytes and endianness, pointers and linked lists, sockets, TCP
streams, framing, binary serialization, non-blocking I/O, `poll()` event
loops, pipelining, chaining hashtables, progressive rehashing, integration
tests and benchmarking. That's real systems
programming. **Congratulations!** 🎉
:::

The repository's `interview-prep.md` has questions and answers about this
exact design. It's a great way to review.
