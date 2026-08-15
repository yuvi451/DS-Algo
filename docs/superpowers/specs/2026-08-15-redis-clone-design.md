# Build Your Own Redis (Chapters 1-8) — Design

Source: https://build-your-own.org/redis/ — chapters 1 through 8 (through
`08b_hashtables_impl.html`), covering everything from raw sockets up to a
key-value server backed by a resizable, chained hashtable with progressive
rehashing.

## Goal

A working, self-contained C implementation of the server + client the book
builds through chapter 8: a TCP key-value store supporting `get`/`set`/`del`
over a custom length-prefixed binary protocol, driven by a poll()-based
non-blocking event loop, backed by a hand-rolled intrusive chaining
hashtable with progressive (incremental) rehashing.

This is **not** RESP-compatible and will not work with `redis-cli` — the
book defines its own wire format (see below). A companion client binary is
built for interacting with the server.

## Language & Platform

C (matching the book's reference implementation), built with `gcc`/`clang`
via a `Makefile`. Targets macOS/Linux; uses `poll()` (not `epoll`), which is
what the book itself uses in chapter 6, so it runs natively on macOS.

## Code Layout

Clean final implementation (no chapter-snapshot files) — one coherent
codebase reflecting where the book lands after chapter 8:

```
Redis/
├── Makefile
├── src/
│   ├── hashtable.h
│   ├── hashtable.c
│   ├── server.c
│   └── client.c
└── test/
    └── test.sh
```

## Wire Protocol (chapters 2-4, extended in ch.7)

Every message (request or response) is framed as:

```
[4 bytes: total length, little-endian] [payload, up to k_max_msg = 4096 bytes]
```

**Request payload** — a command is a list of strings (like argv):

```
[4 bytes: nstr] { [4 bytes: len_i] [len_i bytes: string_i] } * nstr
```

Example: `set foo bar` → `nstr=3`, followed by the three length-prefixed
strings `"set"`, `"foo"`, `"bar"`.

**Response payload** — a status code plus optional data:

```
[1 byte: status] [4 bytes: len] [len bytes: string]   (len/string omitted if not applicable)
```

Status codes:
- `RES_OK` (0) — success, string field holds the result (e.g. `get`'s value)
- `RES_ERR` (1) — unrecognized command or bad arity
- `RES_NX` (2) — key not found (`get`/`del` on a missing key)

The `len`/`string` fields are present only when there's payload beyond the
status byte — since the frame's total length is already known from the
4-byte length prefix, the reader just checks whether any bytes remain
after the status byte and, if so, parses `len`+`string` from them. `set`,
`del`, `RES_NX`, and `RES_ERR` (no message) carry no trailing string;
`get`'s `RES_OK` does.

Malformed frames (declared length > `k_max_msg`, or a request whose
`nstr`/string lengths don't add up to the declared total) cause the server
to close that connection — no partial recovery.

## Event Loop (chapters 5-6)

- `poll()` over a flat `fd → Conn*` array (fd's are small dense ints on
  Unix, so a flat array beats a hashmap here — this is the book's own
  reasoning).
- Each `Conn` holds: `fd`, `want_read`/`want_write` flags, and growable
  `incoming`/`outgoing` byte buffers (`uint8_t*` + size + capacity).
- Non-blocking `accept()`/`read()`/`write()`. Reads append to `incoming`;
  after each read, the server tries to parse as many complete frames out of
  `incoming` as are available (a connection can pipeline multiple
  requests). Each parsed request is dispatched immediately and its
  response appended to `outgoing`. Writes drain `outgoing`, tolerating
  partial writes (poll fires again when the fd is next writable).
- `SIGPIPE` is ignored (or writes use `MSG_NOSIGNAL`) so a client
  disconnecting mid-write doesn't kill the server.

## Hashtable (chapter 8, both parts)

- **Node**: intrusive `struct HNode { HNode *next; uint64_t hcode; }`
  embedded inside `struct Entry { HNode node; char *key; size_t keylen;
  char *val; size_t vallen; }`.
- **Table**: `struct HTab { HNode **tab; size_t mask; size_t size; }` —
  fixed-size array of bucket chains, size always a power of two so
  `hash & mask` replaces `hash % N`.
- **Hash function**: FNV-1a over the key bytes.
- **Resizable wrapper**:
  ```c
  struct HMap { HTab newer; HTab older; size_t migrate_pos; };
  ```
  Normally only `newer` is active. When `newer`'s load factor exceeds 8,
  `older = newer` and a fresh `newer` (double the bucket count) is
  allocated with `calloc` (relying on page-on-demand zeroing to keep this
  fast even for large tables).
- **Progressive rehashing**: `hm_help_rehashing()` moves a small, bounded
  number of entries (e.g. 128) from `older` into `newer` per call, tracking
  progress via `migrate_pos`. It's invoked on every insert and delete so a
  resize completes over many operations instead of one long pause.
- **Insert**: always goes into `newer`; triggers `hm_help_rehashing()`
  first.
- **Lookup/Delete**: check `newer` first, then `older` if not found (and if
  `older` is still non-empty); delete also triggers
  `hm_help_rehashing()`.

## Server Commands

Backed by a single global `HMap`:

- `get <key>` → `RES_OK` + value, or `RES_NX` if absent
- `set <key> <value>` → `RES_OK`, inserts or overwrites
- `del <key>` → `RES_OK` if it existed (and was removed), `RES_NX` if not
- anything else (wrong arity, unknown verb) → `RES_ERR`

## Client

`client.c` takes argv (`./client set foo bar`), encodes it as one request
per the protocol above, sends it over a fresh TCP connection, reads and
decodes exactly one response, and prints the result (or `(nil)` for
`RES_NX`, or the error for `RES_ERR`).

## Testing

`test/test.sh`:
1. Builds the project with `-fsanitize=address -g` (this is hand-rolled C
   memory management — malloc/free in the hashtable — so ASan is the
   primary correctness net, not just a nice-to-have).
2. Starts `server` in the background on a fixed test port.
3. Drives it through `client`: `set`/`get` round-trip, `get` on a missing
   key (expect `NX`), `del` then `get` (expect `NX`), unknown command
   (expect `ERR`).
4. Inserts ~10,000 distinct keys to force at least one resize, then
   re-`get`s a sample of them (including early- and late-inserted keys) to
   confirm progressive rehashing didn't drop or corrupt anything.
5. Shuts the server down and checks its exit/ASan output for errors.

## Build

Single `Makefile` at the repo root:
- `make` — builds `server` and `client` (optimized, `-Wall -Wextra`).
- `make test` — builds the ASan debug variant and runs `test/test.sh`.
- `make clean` — removes build artifacts.

## Out of Scope

Anything from chapter 9 onward: data serialization, AVL trees, sorted
sets, timers/TTL expiration, thread pools. Also out of scope: RESP
protocol compatibility, persistence, replication, auth.
