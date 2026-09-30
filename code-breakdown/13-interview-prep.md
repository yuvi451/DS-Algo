# 13 — Interview Prep: MicroRedis End to End

Everything you need to present this project, draw its design on a
whiteboard, defend its trade-offs, and answer follow-ups. Each section links
back to the detailed file breakdowns.

---

## 1. The pitch

### 30 seconds

> "I built a Redis-style in-memory key-value store in C++. Clients connect
> over TCP and send `get`, `set` and `del` using a length-prefixed binary
> protocol. The server is single-threaded: one event loop uses `poll()` with
> non-blocking sockets to serve many clients at once, so a slow client never
> blocks others. Data lives in a hashtable I wrote from scratch, a chaining
> table that resizes incrementally, the same idea Redis uses, so a resize
> never causes a latency spike. With 200 concurrent clients it sustains
> about 180K operations per second with p99 latency under 2 ms on my laptop."

### 2 minutes (add these)

1. **Protocol:** every message is `[4-byte length][payload]`, because TCP is
   a byte stream with no message boundaries. Requests are a list of
   length-prefixed strings, so keys and values are binary-safe.
2. **Event loop:** each connection has an input and output buffer. When a
   socket is readable I read what's there, process every complete request
   (clients can pipeline), and queue replies. I only ask `poll()` for
   writability when there's something to send.
3. **Hashtable:** intrusive chaining, power-of-two bucket counts so the
   bucket is `hash & mask`, resize at load factor 8. During a resize both
   tables exist, and every insert/delete moves at most 128 entries across.
4. **Testing:** unit tests and an end-to-end test, all under
   AddressSanitizer because the hashtable manages memory manually. A
   multi-threaded load generator for benchmarks.

### Resume bullet check

| Claim | Status |
|---|---|
| Redis-inspired in-memory KV store in C++, many clients over TCP | ✅ |
| Single-threaded, non-blocking event loop, slow client doesn't stall others | ✅ |
| "**epoll** event loop" | ❌ The code uses **`poll()`**. Change the resume to "poll()-based", or be ready to say: "I used poll because I developed on macOS; epoll is Linux-only. Switching is a contained change, and here's what it would buy…" (see §9). |
| Custom chaining hashtable with incremental resizing triggered by load factor | ✅ |
| 200 concurrent clients, 150K+ ops/sec | ✅ Measured ~184K ops/sec, p50 1.0 ms, p99 1.9 ms (Apple M2, loopback) |

Never claim something the code doesn't do. Interviewers often open the repo.

---

## 2. Requirements (how to frame it as system design)

**Functional**
- `set key value` → store or overwrite.
- `get key` → return the value, or "not found".
- `del key` → remove; say whether it existed.
- Many clients connected at the same time.

**Non-functional**
- Low latency per request (microseconds of server time).
- No single slow or idle client can stall others.
- No long pauses, even when the dataset grows (hence incremental resizing).
- Safe against malformed input (bounded message sizes, strict parsing).

**Explicitly out of scope:** persistence, replication, expiry (TTL),
authentication, other data types, RESP compatibility.

---

## 3. Architecture

```
                          ┌───────────────────────────── server process (1 thread) ─────────────────────────────┐
                          │                                                                                      │
 client 1 ──TCP──┐        │   listenFd (127.0.0.1:1234)                                                          │
 client 2 ──TCP──┼──► kernel ─► poll() ──ready fds──► for each ready Conn:                                       │
 client N ──TCP──┘  (sockets,   ▲                      POLLIN  → handleRead → incoming buffer                    │
                    buffers,    │                                 → handleRequests: tryParseFrame → parseRequest │
                    TCP)        │                                 → runCommand → KvStore → HMap                  │
                          │     │                                 → encodeResponse → appendFrame → outgoing      │
                          │     │                      POLLOUT → handleWrite → write(outgoing)                   │
                          │     └──── rebuild pollfd list from conns[] (POLLIN always, POLLOUT if wantWrite) ◄───┘
                          └──────────────────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | File | Responsibility |
|---|---|---|
| Wire protocol | `protocol.{h,cpp}` | Framing, request/response encoding, `Buffer`, blocking client helpers ([02](02-protocol.h.md), [03](03-protocol.cpp.md)) |
| Hashtable | `hashtable.{h,cpp}` | `HMap`: intrusive chaining + incremental resize ([04](04-hashtable.h.md), [05](05-hashtable.cpp.md)) |
| Store | `server.cpp` (`KvStore`) | String API over `HMap`, owns entries |
| Connection | `server.cpp` (`Conn`) | Per-client fd, buffers, flags; RAII closes the fd |
| Event loop | `server.cpp` (`main`) | `poll()`, accept, read/process/write, close ([06](06-server.cpp.md)) |
| Client | `client.cpp` | One command per run, blocking ([07](07-client.cpp.md)) |
| Load generator | `bench/loadtest.cpp` | N threads, closed loop, percentiles ([08](08-loadtest.cpp.md)) |

### Request lifecycle (sequence)

```
client                          kernel                          server loop
  │ socket(), connect() ──────► 3-way handshake ──► backlog
  │                                                   poll: listenFd POLLIN
  │                                                   accept() → fd 5, new Conn (non-blocking)
  │ write(frame "get foo") ───► fd 5 recv buffer
  │                                                   poll: fd 5 POLLIN
  │                                                   read() → incoming
  │                                                   tryParseFrame: Complete
  │                                                   parseRequest → {"get","foo"}
  │                                                   KvStore::get → HMap::lookup
  │                                                   encode + frame → outgoing, wantWrite
  │                                                   poll: fd 5 POLLOUT
  │                          ◄── fd 5 send buffer ◄── write(outgoing)
  │ read() → reply "bar"
  │ close() ──────────────────► FIN
  │                                                   poll: fd 5 POLLIN, read() = 0
  │                                                   Conn destroyed → close(5)
```

### Wire format with real bytes

```
set foo bar   request frame (29 bytes):
  19 00 00 00                      frame length = 25
  03 00 00 00                      nargs = 3
  03 00 00 00 73 65 74             "set"
  03 00 00 00 66 6f 6f             "foo"
  03 00 00 00 62 61 72             "bar"

reply (5 bytes):      01 00 00 00 | 00                 len 1, status Ok
get foo reply (12):   08 00 00 00 | 00 03 00 00 00 62 61 72
get miss reply (5):   01 00 00 00 | 02                 status Nx
```

Limits: payload ≤ 4096 bytes, ≤ 1024 args. Integers are host byte order
(little-endian in practice).

### Concurrency model

- **One thread** does everything. No locks, no data races, no context
  switches between clients. Each command runs to completion before the next
  starts, so every command is automatically **atomic**.
- Concurrency comes from **I/O multiplexing**, not threads: `poll()` tells
  us which sockets are ready, and we never wait on any single socket.
- The trade-off: one CPU core. Any slow command (or slow resize) delays
  every client. That's why the hashtable resizes incrementally.

### Memory and ownership

| Object | Owner | Freed by |
|---|---|---|
| `Conn` | `conns[fd]` (`unique_ptr`) | `conns[fd].reset()` → `~Conn` closes the fd |
| `Entry` | The `HMap` while inside it | `KvStore::del` (after `pop`) or `~HMap` via `entryDelete` |
| Bucket arrays | `HTab::tab` (`std::vector`) | Automatically |
| Buffers | `Conn` members | Automatically with the `Conn` |

### Failure handling

| Event | Handling |
|---|---|
| Client sends frame > 4096 or malformed request | Close that connection |
| Client disconnects (`read` = 0, `POLLHUP`, `POLLERR`) | Close that connection |
| Write to a closed client | `SIGPIPE` ignored → `EPIPE` → close that connection |
| `EAGAIN` on read/write | Try again after the next `poll()` |
| `poll()` interrupted by a signal (`EINTR`) | Loop again |
| `socket`/`bind`/`listen`/`poll` fail | Exit with an error (`die`) |

---

## 4. Deep dive: the event loop

Details in [06](06-server.cpp.md). Points to be able to explain without notes:

1. **Why non-blocking + poll?** A blocking `read()` on one client would
   stall all others. Non-blocking calls return `EAGAIN` instead; `poll()`
   sleeps until *some* socket is ready.
2. **Why per-connection buffers?** TCP delivers partial or merged messages,
   and `write()` can accept part of a reply. The buffers remember
   half-received requests and not-yet-sent replies between loop iterations.
3. **Why only request POLLOUT when needed?** Sockets are almost always
   writable; requesting it permanently makes `poll()` return instantly and
   the loop spins at 100% CPU.
4. **Why a vector indexed by fd?** The OS hands out the lowest free fd, so
   fds are small and dense. Array lookup, no hashing.
5. **Pipelining:** `handleRequests` loops until no complete frame remains,
   so N pipelined requests produce N replies in order.
6. **Level-triggered:** leftover data or pending connections are reported
   again next `poll()`, so reading 64 KB at a time and accepting one
   connection per loop is correct (if not the fastest).

### Complexity per loop iteration

- Building the poll list: O(connections).
- `poll()` itself: O(connections) in the kernel.
- Handling: O(ready connections × work).

With `epoll`/`kqueue` the first two become O(ready connections). That's the
whole reason they exist.

---

## 5. Deep dive: the hashtable

Details in [05](05-hashtable.cpp.md).

1. **Chaining:** each bucket is a singly linked list; insert at head, O(1).
2. **Power-of-two buckets:** `hash & (n - 1)` instead of `hash % n`: one AND
   instead of a division. Requires a hash whose low bits are well mixed
   (FNV-1a is).
3. **Stored hash (`hcode`):** compare hashes before keys (cheap rejection),
   and never recompute hashes during a resize.
4. **Intrusive nodes:** `Entry` inherits `HNode`. One allocation per entry,
   the table is generic without templates, and an entry could later be in
   several structures at once (e.g. a TTL heap).
5. **Pointer-to-pointer lookup:** `htabLookup` returns the address of the
   link pointing at the match, so deletion is `*from = node->next` with no
   head special case.
6. **Incremental resize:** at load factor 8, `newer_` → `older_`, allocate a
   2× table. Each insert/pop moves ≤128 nodes. Lookups check both tables.
   The resize always finishes before the next one is due (moving 8N nodes
   takes 8N/128 ops; the next trigger is 8N inserts away).

### Why not `std::unordered_map`?

It rehashes **everything at once** when it grows. With millions of keys,
that single insert can take tens to hundreds of milliseconds, and in a
single-threaded server every client waits. The project's goal was to learn
and implement Redis's solution.

### Complexity

| Operation | Average | Worst |
|---|---|---|
| `lookup` | O(1) | O(n) if everything collides |
| `insert` | O(1) + ≤128 moves | same |
| `pop` | O(1) + ≤128 moves | same |
| Memory | ~n node pointers + 2 bucket arrays during resize | |

Note: `helpRehashing` doesn't count empty buckets it skips, so one call can
scan many empty buckets. Real Redis bounds that (10 × n empty visits per step).

---

## 6. Design decisions and trade-offs

| Decision | Why | Cost / alternative |
|---|---|---|
| Single thread | No locks, commands are atomic, simple | One core only. Alternative: I/O threads (Redis 6) or a shard per core (Dragonfly, KeyDB). |
| `poll()` | Portable (macOS + Linux), simple | O(n) per call. `epoll`/`kqueue` scale to many idle connections. |
| TCP | Reliable, ordered | Need framing; handshake cost per connection |
| Length-prefix framing | Binary-safe, O(1) to find message end, reject oversize early | Not human-readable; `redis-cli` can't talk to it (RESP is text-ish with length prefixes) |
| 4096-byte max message | Bounds memory per request; protects against huge allocations | Can't store values larger than ~4 KB |
| Host byte order on the wire | Simplest code | Breaks between machines with different endianness; should be fixed little- or big-endian |
| Custom hashtable, incremental resize | No latency spikes | More code than `unordered_map`; lookups check two tables mid-resize |
| Load factor 8 | Less memory, fewer resizes | Longer chains (~8), slower lookups than load factor 1 |
| Intrusive nodes | One allocation, generic, multi-structure | Manual ownership, casts |
| Loopback-only bind | No auth, so don't expose it | Not reachable from other machines |
| Close on malformed input | Can't resync a byte stream after garbage | A buggy client loses all its pipelined replies |

---

## 7. Performance

```
build/loadtest 200 10     (Apple M2, loopback, server and clients on one machine)
throughput=184252.9 ops/sec
latency_us: min=182.1 p50=1017.6 p90=1235.2 p99=1948.8 max=21110.4 mean=1084.0
```

### How to explain the numbers

- **Little's law:** clients in flight = throughput × latency →
  184,000/s × 1.08 ms ≈ 199 ≈ 200 clients ✓. The latency is mostly
  **queueing** behind the other 199 clients, not per-request work.
- **Per-request server cost:** 1 / 184,000 s ≈ **5.4 µs**. That covers one
  `read()`, one `write()`, a share of the `poll()` calls, parsing, one
  hashtable operation, and the kernel's loopback delivery. Syscalls
  dominate, not the hashtable.
- **The ~161K→~184K improvement:** the client used to send the 4-byte header
  and the payload in two `write()` calls. Now it's one: one fewer syscall
  per request on the client, and the server never wakes up for a lone
  header and then needs another `poll()` round for the payload.
- **max 21 ms:** an outlier (the OS descheduling a thread, or a large
  allocation). Not representative, which is why we report percentiles.

### Where time goes, and how to speed it up

| Idea | Why it helps |
|---|---|
| Write immediately after processing | Currently the reply waits for the next `poll()`; most sockets are writable right away, saving a loop iteration per request |
| `epoll`/`kqueue` | Removes the O(n) scan per iteration |
| Accept in a loop until `EAGAIN` | Handles connection bursts faster |
| Read offset instead of `vector::erase` | `consume` is O(remaining bytes); pipelined traffic becomes O(n²) |
| Batch many replies per `write` | Already happens naturally with pipelining |
| Avoid copying the key into a probe | Saves an allocation per operation for long keys |

### Benchmark caveats

Server and 200 client threads share one machine's CPU; loopback has no real
network delay; values are tiny. Say this before the interviewer does.

---

## 8. Known limitations (and fixes)

| Limitation | Consequence | Fix |
|---|---|---|
| No backpressure: always reads, `outgoing` unbounded | A client that pipelines forever but never reads makes the server's memory grow without limit | Stop reading (drop `POLLIN`) when `outgoing` exceeds a threshold, or disconnect (Redis: `client-output-buffer-limit`) |
| `Buffer::consume` erases from the front | O(n²) with deep pipelining | Keep a read offset and compact occasionally, or a ring buffer |
| Empty value looks like "no value" | `get` of `""` prints `OK` | Always encode the length for `get` replies, or a distinct status |
| Replies dropped on half-close / malformed input | Pipelining client loses earlier replies | Flush `outgoing` before closing |
| No idle timeout | Idle connections hold fds forever | Track last activity; close after N seconds (Redis `timeout`) |
| fd exhaustion (`EMFILE`) | `accept` fails but the listener stays "readable" → `poll` returns instantly → 100% CPU spin | Stop polling the listener temporarily, or keep a spare fd to accept-and-close |
| One accept per loop | Slow under connection bursts | Accept until `EAGAIN` |
| Host byte order | Endianness-dependent protocol | Define little-endian explicitly |
| Hashtable never shrinks | Memory stays high after mass deletes | Shrink when load drops (Redis: below 10%) |
| FNV-1a is not keyed | Hash-flooding attack possible | SipHash with a random key (what Redis does) |
| No TTL, persistence, replication | Data lost on restart | See §9 |

---

## 9. "How would you make this production-ready / scale it?"

Go layer by layer. Mention what real Redis does.

**Single node, more connections**
- `epoll` (Linux) / `kqueue` (macOS): O(ready) instead of O(all). Redis's
  `ae` event library picks the best one per OS.
- Idle timeouts, max client count, per-client input/output buffer limits.

**Single node, more CPU**
- Keep command execution single-threaded but move socket reads/writes and
  parsing to I/O threads (Redis 6+).
- Or shared-nothing: one event loop + one hashtable **per core**, keys
  partitioned by hash (Dragonfly, KeyDB-style designs).

**Durability**
- **Snapshots (RDB):** `fork()` the process; the child writes the whole
  dataset to disk while the parent keeps serving. The OS's copy-on-write
  makes the fork cheap.
- **Append-only file (AOF):** log every write command; `fsync` every write
  (safe, slow), every second (usual), or never (fast, risky). Replay on
  restart; rewrite periodically to compact.

**Availability**
- **Replication:** primary sends its write stream to replicas asynchronously;
  replicas serve reads and can be promoted on failure (Redis Sentinel
  automates failover).

**More data than one machine**
- **Sharding:** Redis Cluster splits keys into 16,384 hash slots
  (`CRC16(key) mod 16384`), each owned by one primary. Clients are redirected
  (`MOVED`) to the right node. Consistent hashing is the other classic answer.

**Features**
- **TTL:** store an expiry time per key; delete lazily on access, and
  actively by sampling in the background (Redis) or with a min-heap of
  deadlines (the book's approach).
- **Eviction under memory pressure:** approximate LRU/LFU by sampling a few
  keys and evicting the best candidate.
- **Security:** authentication, TLS, bind to specific interfaces.
- **Other data types:** lists, sets, sorted sets (skip list + hash table;
  the book uses an AVL tree).

---

## 10. MicroRedis vs real Redis

| | MicroRedis | Redis |
|---|---|---|
| Protocol | Binary length-prefixed | RESP (text-ish, length-prefixed bulk strings, `\r\n`) |
| Event loop | `poll()` | `ae`: epoll / kqueue / evport / select |
| Threads | 1 | 1 for commands, optional I/O threads |
| Hashtable | 2 tables, incremental rehash, 128 nodes/op | 2 tables, incremental rehash, 1 bucket/op + background rehash in idle time |
| Resize trigger | Load factor 8 | ~Load factor 1 (grow), <10% (shrink) |
| Hash | FNV-1a | SipHash (keyed) |
| Commands | get/set/del | Hundreds, many data types |
| Persistence / replication / cluster | None | RDB, AOF, replicas, Cluster |

The core idea, **single-threaded event loop + incrementally rehashed
hashtable**, is exactly Redis's.

---

## 11. Likely interview questions (with answers)

### About the project

**Q: Why single-threaded? Isn't that slow?**
Most operations take microseconds of CPU; the bottleneck is I/O and syscalls,
not computation. One thread means no locks, no races, and every command is
atomic. Redis made the same choice. The limit is one core; to go beyond it,
use I/O threads or shard across cores/processes.

**Q: How does one thread serve 200 clients "at the same time"?**
It never waits on any single client. Sockets are non-blocking, and `poll()`
reports which ones are ready. The thread handles ready clients one by one;
each request takes microseconds, so to clients it looks simultaneous.
Concurrency, not parallelism.

**Q: What happens if a client connects and never sends anything?**
Nothing bad. Its socket is never reported readable, so it costs one poll
entry and one fd. (Without an idle timeout it holds them forever.)

**Q: What if a client sends half a request and stalls?**
The half stays in `incoming`; `tryParseFrame` returns `Incomplete`, and the
server moves on. When the rest arrives, the request completes.

**Q: What if a client sends a huge length?**
`tryParseFrame` rejects any length > 4096 as soon as the 4-byte header
arrives, and the connection is closed. No allocation happens.

**Q: What if a client never reads its replies?**
Its replies pile up in `outgoing` with no limit. That's the missing
backpressure. Fix: stop reading from that client above a threshold, or
disconnect it.

**Q: Why did you write your own hashtable?**
To avoid resize pauses. `std::unordered_map` rehashes everything at once;
mine spreads the work across operations. That matters in a single-threaded
server, where any pause stalls every client.

**Q: Walk me through a resize.**
At 8 entries per bucket, the current table becomes `older_` and a table
twice as big becomes `newer_`. New inserts go to `newer_`. Every insert or
delete moves up to 128 entries from `older_`, bucket by bucket, using the
stored hash. Lookups check `newer_` then `older_`. When `older_` is empty it's
freed.

**Q: Can a second resize start before the first finishes?**
No: `insert` only starts a resize when `older_` is empty (and
`startResizing` asserts it). Mathematically it can't be needed anyway: the
migration finishes in 1/128th of the inserts that would trigger the next one.

**Q: Why powers of two?**
`hash & (n-1)` equals `hash % n` but is one AND instruction. The downside is
that only the low bits of the hash pick the bucket, so the hash must mix
well.

**Q: What's an intrusive data structure?**
The link fields live *inside* the user's object (`Entry` inherits `HNode`)
instead of the container allocating separate nodes. One allocation per
entry, and the same object can be in several containers.

**Q: How did you test it?**
Unit tests for the hashtable (including forced collisions and 5,000 keys
through 8 resizes) and protocol (round-trips, truncated/oversized input,
real socket I/O via `socketpair`); an end-to-end bash test with 10,000
inserts through the real client and server; everything under
AddressSanitizer. Plus the load generator.

**Q: How did you measure 184K ops/sec?**
200 threads, each with one persistent connection, alternating set/get in a
closed loop for 10 s, timing each round trip with `steady_clock`. Throughput
= completed requests ÷ elapsed time; percentiles from the sorted latencies.
Little's law cross-checks it.

**Q: What would you change first?**
Backpressure (a real memory-safety issue), then writing replies immediately
instead of waiting for the next poll, then epoll/kqueue.

**Q: You converted this from C to C++. What changed?**
Language only, not behaviour: RAII (`unique_ptr<Conn>`, destructors close
fds and free entries), `std::vector`/`std::string` instead of malloc'd
buffers, `std::optional` and `enum class` instead of sentinel values. The
hashtable and event loop stayed hand-written on purpose. Verified by
running the old client against the new server and re-running the tests and
benchmark.

### Networking

**Q: TCP vs UDP — why TCP?**
A database can't lose or reorder writes. TCP gives reliable, ordered
delivery. UDP would force us to re-implement that.

**Q: Why do you need framing if TCP is reliable?**
Reliable ≠ message-preserving. TCP is a byte stream: two writes can arrive
as one read, or one write as several reads. The length prefix marks where
each message ends.

**Q: Explain the TCP handshake and where it happens in your code.**
SYN → SYN-ACK → ACK. The client's `connect()` performs it; on the server the
kernel completes it and queues the connection in the listen backlog;
`accept()` just takes a finished connection from the queue.

**Q: What does `listen()`'s backlog do?**
Sets the maximum queue of completed-but-not-yet-accepted connections.
`SOMAXCONN` = system max (128 on macOS).

**Q: What's the difference between the listening socket and connection sockets?**
The listening socket only produces new connections via `accept()`. Each
accepted client gets its own socket (fd) that carries its data.

**Q: What does `read()` returning 0 mean?**
EOF: the peer closed its sending side (sent FIN). We close the connection.

**Q: Blocking vs non-blocking I/O?**
Blocking calls sleep until they can make progress; non-blocking ones return
`EAGAIN` immediately. Servers use non-blocking I/O plus a readiness API so
one thread never sleeps on one client.

**Q: select vs poll vs epoll vs kqueue?**
`select`: bitmap, max 1024 fds, O(n). `poll`: array, no fd limit, O(n) per
call. `epoll` (Linux) / `kqueue` (BSD/macOS): register once, the kernel
tracks readiness and returns only ready fds, O(ready). Needed for tens of
thousands of connections (the C10K problem).

**Q: Level-triggered vs edge-triggered?**
Level: reported while the condition holds (poll, default epoll); forgiving.
Edge: reported when it changes (`EPOLLET`); you must drain until `EAGAIN` or
you'll miss data. Faster, trickier.

**Q: Why ignore SIGPIPE?**
Writing to a socket whose peer closed sends SIGPIPE, which kills the process
by default. Ignoring it turns that into an `EPIPE` error we handle per
connection.

**Q: What's TIME_WAIT and why SO_REUSEADDR?**
The side that closes first keeps the connection in TIME_WAIT for 2×MSL
(30 s on macOS) so delayed packets can't corrupt a new connection with the
same 4-tuple. `SO_REUSEADDR` lets a restarted server bind its port despite
old connections in TIME_WAIT.

**Q: What's Nagle's algorithm / TCP_NODELAY?**
Nagle delays small writes while earlier data is unacknowledged, to batch
them. Combined with delayed ACKs it can add tens of ms to request/response
traffic. `TCP_NODELAY` disables it; the client sets it and sends each
request in a single `write`.

**Q: Why `htons`?**
Socket addresses must be in network byte order (big-endian); x86/ARM are
little-endian. (My own length fields use host order, a known simplification.)

**Q: What's the 4-tuple? How can 200 clients share port 1234?**
A connection is identified by (client IP, client port, server IP, server
port). Each client gets a different ephemeral port, so every connection is
unique.

**Q: What's 127.0.0.1 vs 0.0.0.0?**
Loopback (this machine only) vs all interfaces. Binding to loopback keeps an
unauthenticated database off the network.

**Q: What's pipelining and does your server support it?**
Sending multiple requests without waiting for replies. Yes: the server
processes every complete frame in its buffer and replies in order; TCP
preserves ordering.

**Q: What happens when the kernel send buffer is full?**
Non-blocking `write` returns a partial count or `EAGAIN`. We keep the rest in
`outgoing`, request `POLLOUT`, and continue when `poll` says there's room.

**Q: What's a Unix domain socket?**
A socket between processes on the same machine (`AF_UNIX`), addressed by a
file path, no TCP/IP. Faster than loopback TCP. My protocol test uses
`socketpair(AF_UNIX, SOCK_STREAM)`.

### C++

**Q: Where do you use RAII?**
`Conn` closes its fd in its destructor; `conns` holds `unique_ptr<Conn>`, so
`reset()` closes a connection. `HMap`'s destructor frees remaining entries.
Buffers and bucket arrays are `std::vector`s.

**Q: Why are copy constructors deleted on `Conn` and `HMap`?**
Copies would share the same fd / node pointers and both would close/free
them: double close or double free.

**Q: Why `static_cast` from `HNode*` to `Entry*`? Is it safe?**
It's a downcast from base to derived. Safe because only `Entry` objects are
ever inserted into that map. It's unchecked; `dynamic_cast` would check at
runtime but needs virtual functions.

**Q: Why `memcpy` to read integers from the buffer?**
Fields can be unaligned, and reading bytes through a `uint32_t*` violates
strict aliasing. `memcpy` is well-defined and compiles to a single load.

**Q: Why `std::optional` instead of exceptions?**
Parse failures are expected (untrusted input), not exceptional; the caller
checks and closes the connection. No exception-safety reasoning needed in
the event loop.

**Q: What does AddressSanitizer catch?**
Use-after-free, heap/stack buffer overflows, double free, memory leaks. It
instruments memory accesses at compile time (~2× slowdown), which is why
it's for tests only.

---

## 12. CN rapid-revision sheet

| Concept | One-liner |
|---|---|
| Layers | App (our protocol) → Transport (TCP) → Network (IP) → Link |
| IP / port | Machine / program on the machine |
| 4-tuple | Identifies a TCP connection |
| TCP | Reliable, ordered **byte stream**, connection-oriented |
| UDP | Unreliable datagrams, keeps message boundaries |
| Handshake | SYN, SYN-ACK, ACK; `connect()` / backlog / `accept()` |
| Close | FIN each way; `read()` = 0 is EOF; RST = abort |
| TIME_WAIT | Active closer waits 2×MSL; `SO_REUSEADDR` for servers |
| Framing | Needed because TCP has no message boundaries |
| Kernel buffers | `write` copies into send buffer; partial reads/writes are normal |
| Non-blocking | `EAGAIN` instead of sleeping |
| Multiplexing | `select` / `poll` O(n); `epoll` / `kqueue` O(ready) |
| Level vs edge | Reported while true vs when it changes |
| Byte order | Network = big-endian; `htons` / `htonl` |
| Nagle / NODELAY | Batch small writes / send immediately |
| SIGPIPE | Kills on write to closed socket unless ignored |
| Backlog | Queue of completed, un-accepted connections |
| Loopback | 127.0.0.1, never leaves the machine |
| Little's law | concurrency = throughput × latency |
| Pipelining | Many requests in flight on one connection, replies in order |

---

## 13. Numbers to remember

| | Value |
|---|---|
| Port | 1234 (real Redis: 6379) |
| Max message | 4096 bytes |
| Max args | 1024 |
| Initial buckets | 4 |
| Max load factor | 8 |
| Rehash work | 128 nodes per insert/pop |
| Read chunk | 64 KB |
| Benchmark | 200 clients, ~184K ops/s, p50 ~1.0 ms, p99 ~1.9 ms |
| Server cost per request | ~5 µs |
| Code size | ~1,150 lines including tests |
