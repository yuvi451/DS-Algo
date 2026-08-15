# C++ Conversion of the Redis Clone — Design

## Goal

Convert the existing C implementation (chapters 1-8 of build-your-own.org/redis:
`src/hashtable.{h,c}`, `src/protocol.{h,c}`, `src/server.c`, `src/client.c`,
`bench/loadtest.c`, `test/test_hashtable.c`, `test/test_protocol.c`) to
idiomatic C++, in place. This is a language/style port, not a behavior
change: the wire protocol, the hashtable's algorithm (intrusive chaining,
progressive rehashing, load factor 8), and the event loop's model
(`poll()`, non-blocking, want_read/want_write) are preserved exactly. A C
client and a C++ server (or vice versa) would still interoperate, because
nothing about what goes on the wire changes.

The hand-rolled hashtable and the hand-rolled `poll()` event loop are kept
hand-rolled — replacing them with `std::unordered_map` or a thread-per-connection
model would delete the exact material (chapters 5-8) this project exists to
learn from. Everything *around* those two things is modernized: RAII
instead of manual malloc/free, `std::string`/`std::vector` instead of
malloc'd buffers, classes instead of free functions mutating globals,
`std::optional`/enum-class returns instead of NULL/-1 sentinels.

## Language & Toolchain

C++17 (widely supported by both clang and gcc; gives us `std::optional`,
`std::string_view`, structured bindings, `if`-with-initializer — everything
this conversion needs without reaching for C++20). Compiler invoked as
`c++`/`g++`/`clang++` (whichever `CXX` resolves to). Source files become
`.cpp`; headers stay `.h` (common C++ convention, avoids unnecessary
churn). Old `.c` files are deleted as their `.cpp` replacements land — this
is a conversion, not a fork; the C sources do not persist alongside the
C++ ones.

## Global Constraints (unchanged from the original project)

- Wire protocol byte-for-byte unchanged: `[4-byte LE length][payload]`,
  `K_MAX_MSG = 4096`, request = `[4-byte nstr]{[4-byte len_i][bytes]}*`,
  response = `[1-byte status][4-byte len][bytes]` (len/data omitted when
  absent), status codes `RES_OK=0`/`RES_ERR=1`/`RES_NX=2`.
- Server listens on `127.0.0.1:1234` (`SERVER_PORT`), `poll()` only (no
  epoll/kqueue), SIGPIPE ignored.
- Hashtable: intrusive chaining, power-of-two bucket counts, resize at
  load factor 8, progressive rehashing moving 128 entries/call, FNV-1a
  hash.
- No `-DNDEBUG` in any build; test binaries (unit + integration) built
  with `-fsanitize=address`.
- No new external dependencies (no test framework, no Boost, etc.) — the
  standard library is the only addition versus the C version.
- No exceptions used for protocol/parse error handling (per the earlier
  decision) — errors stay return-code/`std::optional`/enum-class shaped,
  so the event loop's per-connection error handling doesn't need
  exception-safety reasoning.

## Module Design

### `src/hashtable.h` / `src/hashtable.cpp`

```cpp
struct HNode {
    HNode *next = nullptr;
    uint64_t hcode = 0;
};

using EqFn = bool (*)(const HNode *a, const HNode *b);
using DeleteFn = std::function<void(HNode *)>;

class HMap {
public:
    HMap(EqFn eq, DeleteFn deleter);
    ~HMap();  // walks any remaining nodes through deleter_, frees bucket arrays

    HMap(const HMap &) = delete;
    HMap &operator=(const HMap &) = delete;

    void insert(HNode *node);
    HNode *lookup(const HNode *key) const;
    HNode *pop(const HNode *key);
    size_t size() const;

private:
    struct HTab { std::vector<HNode *> tab; size_t mask = 0; size_t size = 0; };
    void helpRehashing();
    void startResizing();

    EqFn eq_;
    DeleteFn deleter_;
    HTab newer_, older_;
    size_t migratePos_ = 0;
};

uint64_t hashBytes(const uint8_t *data, size_t len);  // FNV-1a, unchanged
```

`eq_` is stored once at construction instead of passed to every call —
every call site in this project always passes the same predicate, so this
removes repetition without changing behavior. `HTab::tab` becomes
`std::vector<HNode*>` (still manually indexed by `hash & mask`, still
manually chained via `HNode::next` — this is *not* switched to
`std::unordered_map`; only the raw bucket array's allocation is now
vector-managed instead of `calloc`/`free`'d by hand). The resize-in-flight
guard (`older_.tab` non-empty ⇒ don't start a second resize), the
128-entries-per-`helpRehashing()` batch, and lookup checking `newer_` then
`older_` are unchanged algorithmically — this is the same code, typed as
methods.

### `src/protocol.h` / `src/protocol.cpp`

```cpp
constexpr size_t K_MAX_MSG = 4096;
constexpr uint16_t SERVER_PORT = 1234;

enum class ResponseStatus : uint8_t { Ok = 0, Err = 1, Nx = 2 };

class Buffer {
public:
    void append(const uint8_t *data, size_t len);
    void append(std::string_view s);
    void consume(size_t n);
    const uint8_t *data() const;
    size_t size() const;
private:
    std::vector<uint8_t> buf_;
};

// Request: nstr + length-prefixed strings, same as today.
bool encodeRequest(Buffer &out, const std::vector<std::string> &args);  // false if > K_MAX_MSG
std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len);

// Response: status + optional length-prefixed string.
void encodeResponse(Buffer &out, ResponseStatus status, std::string_view data = {});
struct Response { ResponseStatus status; std::string data; };
std::optional<Response> parseResponse(const uint8_t *data, size_t len);

// Frame layer.
enum class FrameStatus { Incomplete, Malformed, Complete };
struct FrameInfo { size_t frameLen; size_t payloadOff; size_t payloadLen; };
FrameStatus tryParseFrame(const uint8_t *buf, size_t bufLen, FrameInfo &out);

bool readFull(int fd, uint8_t *buf, size_t n);
bool writeAll(int fd, const uint8_t *buf, size_t n);
std::optional<Buffer> readFrame(int fd);          // full frame incl. 4-byte header, as today
bool writeFrame(int fd, const uint8_t *payload, size_t len);
```

`FrameStatus` is a three-way enum rather than `std::optional` specifically
because the event loop needs to distinguish "not enough data yet, wait for
more" (`Incomplete`) from "the client sent garbage, close the connection"
(`Malformed`) — those are different actions in `server.cpp`, and
`std::optional` can only represent "value or nothing," which would
collapse that distinction. `parseRequest`/`parseResponse` *can* use
`std::optional` because both their failure cases (any kind of malformed
input) are handled identically by the caller (reject).

`encodeRequest`/`parseRequest` operating on `std::vector<std::string>`
removes `free_request_args` entirely — ownership is automatic. Byte
layout on the wire is unchanged (`nstr` + per-string `len`+bytes).

### `src/server.cpp`

```cpp
class KvStore {
public:
    KvStore();
    ~KvStore();  // deletes any remaining Entry objects via the HMap deleter

    std::optional<std::string> get(std::string_view key) const;
    void set(std::string_view key, std::string_view val);
    bool del(std::string_view key);  // true if it existed

private:
    HMap map_;  // constructed with entryEq and a deleter that `delete`s Entry*
};

class Entry : public HNode {
public:
    std::string key, val;
};

class Conn {
public:
    explicit Conn(int fd);   // arms O_NONBLOCK
    ~Conn();                 // closes fd

    Conn(const Conn &) = delete;
    Conn &operator=(const Conn &) = delete;

    int fd() const;
    bool wantRead = true, wantWrite = false, wantClose = false;
    Buffer incoming, outgoing;
};
```

`std::vector<std::unique_ptr<Conn>> g_fd2conn` replaces the manually
`realloc`'d `Conn**` array; growing it is `resize()`, and tearing down a
connection is `g_fd2conn[fd].reset()` — `Conn`'s destructor closes the fd,
and `Buffer`'s destructor (via its internal `vector`) frees both buffers.
No more `conn_destroy()` function. The `poll()` loop itself — building the
`pollfd` array from `wantRead`/`wantWrite`, handling `EAGAIN`/partial
writes, framing responses with a 4-byte length prefix before appending to
`outgoing` (the fix from the original C build) — is unchanged in
structure, just operating on these types. `do_get`/`do_set`/`do_del`
become `KvStore` methods; the free function that used to be `do_request`
becomes a small dispatcher that pattern-matches on `args[0]`/arity and
calls the matching `KvStore` method, then `encodeResponse`s the result.

### `src/client.cpp`

`argv` → `std::vector<std::string>` (skipping `argv[0]`), uses
`encodeRequest`/`writeFrame`/`readFrame`/`parseResponse` from the new
protocol API, prints via `std::cout`/`std::cerr` instead of
`printf`/`fwrite`. Same four output shapes as today: the value, `OK`,
`(nil)`, `(error) ...`.

### `bench/loadtest.cpp`

Same closed-loop design (N threads, each holding one persistent
connection, alternating `set`/`get`, timing each round trip) but
`std::thread`/`std::vector<std::thread>` instead of raw
`pthread_create`/`pthread_join`, `std::chrono::steady_clock` instead of
`clock_gettime`, `std::vector<double>` for latency samples, `std::sort`.
Same CLI (`loadtest <n_clients> <duration_sec>`), same output format
(throughput + min/p50/p90/p99/max/mean latency).

### Tests

`test/test_hashtable.cpp`, `test/test_protocol.cpp`: same test cases as
the C versions (insert/lookup, delete, forced-collision chaining,
progressive-rehash-with-concurrent-delete for hashtable; buffer
growth/consume, request/response round-trips, truncated/oversized-frame
rejection, socketpair-based frame IO for protocol), ported to the new
typed APIs. `TestNode : public HNode` mirrors `Entry`'s inheritance
approach. Still plain `assert()`-based — no test framework is introduced.
`test/test_integration.sh` is unchanged (it only shells out to the built
binaries; nothing about the wire protocol changed).

### Makefile

Same target names and same three-tier build shape (release `all`, ASan
`test-*`/`*_asan`) as today, retargeted at `.cpp` sources and a C++
compiler:

```makefile
CXX := c++
CXXFLAGS := -std=c++17 -Wall -Wextra
RELEASE_FLAGS := -O2
ASAN_FLAGS := -fsanitize=address -g
```

Adds one new target, `bench`, building `build/loadtest` from
`bench/loadtest.cpp` + `src/protocol.cpp` (`-pthread` for `std::thread`).

## Verification Plan

1. Unit tests: `make test-hashtable && make test-protocol` — same
   assertions as the C version, now exercised through the C++ API.
2. Manual smoke sequence (same as the original project's Task 3):
   `get`/`set`/`get`/`set`/`get`/`del`/`get`/unknown-command against a
   freshly built `build/server` + `build/client`, output compared
   line-for-line against the original C build's output.
3. Full integration suite: `make clean && make test` — ASan binaries,
   10,000-key insert forcing a resize, sampled-key survival check, zero
   ASan errors.
4. Performance regression check: `build/loadtest 200 10` against the new
   C++ server, compared against the C baseline already measured
   (~160,000 ops/sec, p50 ≈1.2ms at 200 concurrent clients). Not expected
   to regress meaningfully — the hot path (hashtable, poll loop) is
   algorithmically identical — but this is checked, not assumed.

## Out of Scope

Everything the original project already excluded (chapters 9+:
serialization, AVL trees, sorted sets, TTL, thread pool, persistence,
replication, auth, RESP compatibility) remains excluded. This conversion
does not add new functionality, does not change the wire protocol, and
does not introduce templates/generics into the hashtable (it stays a
single concrete `HMap` operating on `HNode*`, matching the book's
intrusive, non-generic style).
