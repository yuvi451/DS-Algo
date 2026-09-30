# MicroRedis

A small Redis-like in-memory key-value server in C++17, following chapters 1–8
of [Build Your Own Redis](https://build-your-own.org/redis/). It supports
`get`, `set` and `del` over TCP using its own binary protocol (not RESP, so
`redis-cli` won't work). There are no dependencies beyond the standard library.

## Build and run

```sh
make                         # build/server and build/client
build/server                 # listens on 127.0.0.1:1234

build/client set foo bar     # OK
build/client get foo         # bar
build/client del foo         # OK
build/client get foo         # (nil)
```

| Target | What it does |
|---|---|
| `make` | Release build of the server and client (`-O2`) |
| `make test` | Unit tests plus the integration test, all built with AddressSanitizer |
| `make bench` | Builds `build/loadtest` |
| `make clean` | Removes `build/` |

The integration test starts the ASan server and runs about 10,000 client
commands to force several hashtable resizes, so it takes about a minute.

## Layout

```
src/hashtable.{h,cpp}   HMap: intrusive chained hashtable with incremental resizing
src/protocol.{h,cpp}    Buffer, message encoding/parsing, framing, blocking client I/O
src/server.cpp          KvStore, per-connection state, poll() event loop
src/client.cpp          Sends one command per run and prints the reply
bench/loadtest.cpp      Multi-threaded load generator
test/                   Unit tests (plain assert) and test_integration.sh
code-breakdown/         Line-by-line walkthrough, networking refresher, interview prep
```

## Design

### Event loop (`server.cpp`)
A single thread runs a `poll()` loop over non-blocking sockets. Each `Conn`
holds an `incoming` and an `outgoing` buffer. When a socket is readable, the
server reads up to 64 KB and handles every complete request in `incoming`
(clients may pipeline). Each reply is framed and appended to `outgoing`.
`POLLOUT` is requested only while `outgoing` has data, and partial writes are
resumed on the next loop. Connections are stored in a vector indexed by fd.
`SIGPIPE` is ignored.

### Hashtable (`hashtable.cpp`)
- Nodes are intrusive: `Entry` inherits from `HNode` (`next` and `hcode`),
  so the table never allocates per entry.
- Bucket counts are powers of two, so a key's bucket is `hash & mask`. The
  hash is FNV-1a.
- When the average reaches 8 entries per bucket, the table becomes `older_`
  and a new table twice the size becomes `newer_`. Every `insert` and `pop`
  then moves up to 128 entries across, so no single call pays for a full
  resize. Lookups check `newer_` first, then `older_`.

### Wire protocol (`protocol.h`)
Integers are 32-bit, in host byte order (little-endian on x86/ARM).

```
frame:     [len][payload]                  len <= 4096
request:   [nargs] { [len][bytes] } * nargs    nargs <= 1024
response:  [status:1 byte] [len][bytes]        len/bytes omitted if there's no data
status:    0 = OK, 1 = ERR, 2 = NX (key not found)
```

| Command | Reply |
|---|---|
| `get k` | OK with the value, or NX |
| `set k v` | OK |
| `del k` | OK if the key existed, else NX |
| anything else | ERR |

The server closes the connection on an oversized frame or a request whose
lengths don't add up.

## Benchmark

```sh
make all bench
build/server &
build/loadtest 200 10        # 200 clients, 10 seconds
```

Each client thread keeps one connection open and alternates `set`/`get`,
waiting for each reply before sending the next. Measured on an Apple M2
MacBook Pro over loopback:

```
throughput=184252.9 ops/sec
latency_us: min=182.1 p50=1017.6 p90=1235.2 p99=1948.8 max=21110.4
```

## Known limitations

- An empty value can't be told apart from no value: after `set k ""`, `get k`
  prints `OK`.
- `Buffer::consume` erases from the front of a vector, which is O(n) per call.
- No backpressure: a client that sends requests without reading replies makes
  its `outgoing` buffer grow without limit.
- Replies still queued when a client closes its end are dropped.
- Not implemented (book chapters 9+): TTL, sorted sets, persistence, thread pool.
