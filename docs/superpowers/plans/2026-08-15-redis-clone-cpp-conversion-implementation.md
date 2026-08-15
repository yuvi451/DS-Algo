# C++ Conversion of the Redis Clone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the existing C implementation (chapters 1-8 of
build-your-own.org/redis) to idiomatic C++, in place, with no behavior
change: same wire protocol, same hashtable algorithm, same event-loop
model.

**Architecture:** Four modules converted bottom-up — `hashtable`,
`protocol`, `server`+`client`, `bench`/final wiring — each producing a
compiling, passing deliverable via its own test target. The hand-rolled
hashtable and `poll()` event loop are kept hand-rolled (classes instead of
structs+free-functions); `Buffer`/request/response data now use
`std::vector`/`std::string`/`std::optional` instead of malloc'd arrays.

**Tech Stack:** C++17, POSIX sockets/`poll()`, `std::thread` (bench tool
only), GNU Make. No new external dependencies.

## Global Constraints

- C++17, compiled as `c++`/`g++`/`clang++` via `$(CXX)`. Headers stay
  `.h`; implementation files are `.cpp`.
- Wire protocol byte-for-byte unchanged: `[4-byte LE length][payload]`,
  `K_MAX_MSG = 4096`; request = `[4-byte nstr]{[4-byte len_i][bytes]}*`;
  response = `[1-byte status][4-byte len][bytes]` (len/data omitted when
  absent); status codes `Ok=0`/`Err=1`/`Nx=2`.
- Server listens on `127.0.0.1:1234` (`SERVER_PORT`), `poll()` only (no
  epoll/kqueue), `SIGPIPE` ignored.
- Hashtable: intrusive chaining (`Entry : public HNode`), power-of-two
  bucket counts, resize at load factor 8, progressive rehashing moving
  128 entries/call, FNV-1a hash (`hashBytes`). Not templated/generic —
  stays a single concrete `HMap` operating on `HNode*`.
- No `-DNDEBUG` in any build; test binaries (unit + integration) built
  with `-fsanitize=address`.
- No exceptions for protocol/parse error handling — errors are
  `std::optional`/enum-class/bool return values, never `throw`.
- No new external dependencies (no test framework, no Boost).
- **Known transitional breakage:** deleting `src/hashtable.c` in Task 1
  breaks `make all`, `make test-integration`, and `make server_asan`/
  `client_asan` (they reference a now-missing prerequisite file) — this
  is expected and gets progressively worse through Task 2 (protocol.c
  also gone) until Task 3 restores full parity by finishing the
  server/client conversion and fixing every remaining Makefile rule in
  one pass. Each task's own verification step tells you exactly which
  `make` targets to run — do not attempt to fix targets outside your
  task's scope; that breakage is expected and Task 3 resolves it.
- Performance baseline (for Task 4's regression check): the C version,
  load-tested with `bench/loadtest 200 10` (200 concurrent clients, 10s,
  closed-loop `set`/`get`), sustained ~160,000 ops/sec with p50 latency
  ≈1.2ms. The author re-verified this exact design compiles and holds
  the same throughput (~159,000 ops/sec) in C++ before writing this plan
  — Task 4 reproduces that check formally.

---

## Task 1: Hashtable module

**Files:**
- Delete: `src/hashtable.c`, `test/test_hashtable.c`
- Modify: `src/hashtable.h` (full rewrite), `Makefile` (test-hashtable
  rule only)
- Create: `src/hashtable.cpp`, `test/test_hashtable.cpp`

**Interfaces:**
- Produces (used by Task 3's `server.cpp` and by
  `test/test_hashtable.cpp`):
  - `struct HNode { HNode *next = nullptr; uint64_t hcode = 0; };`
  - `using EqFn = bool (*)(const HNode *a, const HNode *b);`
  - `using DeleteFn = std::function<void(HNode *)>;`
  - `class HMap` — constructor `HMap(EqFn eq, DeleteFn deleter)`;
    `void insert(HNode *node)`; `HNode *lookup(const HNode *key) const`;
    `HNode *pop(const HNode *key)`; `size_t size() const`; destructor
    walks any remaining nodes through `deleter` then frees bucket arrays.
    Non-copyable.
  - `uint64_t hashBytes(const uint8_t *data, size_t len);` (FNV-1a)
- Consumes: nothing (this module has no dependencies beyond the standard
  library).

- [ ] **Step 1: Delete the old C files and write the failing C++ test**

```bash
rm src/hashtable.c test/test_hashtable.c
```

Create `test/test_hashtable.cpp`:

```cpp
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include "../src/hashtable.h"

struct TestNode : public HNode {
    int key;
    int val;
};

static bool testEq(const HNode *a, const HNode *b) {
    return static_cast<const TestNode *>(a)->key == static_cast<const TestNode *>(b)->key;
}

static void deleteTestNode(HNode *n) {
    delete static_cast<TestNode *>(n);
}

static TestNode *makeNode(int key, int val) {
    auto *n = new TestNode();
    n->key = key;
    n->val = val;
    n->hcode = hashBytes(reinterpret_cast<const uint8_t *>(&key), sizeof(key));
    return n;
}

static TestNode *find(HMap &map, int key) {
    TestNode probe{};
    probe.key = key;
    probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(&key), sizeof(key));
    HNode *found = map.lookup(&probe);
    return found ? static_cast<TestNode *>(found) : nullptr;
}

static void testInsertAndLookup() {
    HMap map(testEq, deleteTestNode);

    TestNode *n = makeNode(42, 100);
    map.insert(n);

    TestNode *found = find(map, 42);
    assert(found != nullptr);
    assert(found->val == 100);
    assert(find(map, 99) == nullptr);

    printf("testInsertAndLookup: OK\n");
}

static void testDelete() {
    HMap map(testEq, deleteTestNode);

    TestNode *n = makeNode(7, 77);
    map.insert(n);
    assert(map.size() == 1);

    TestNode probe{};
    probe.key = 7;
    probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(&probe.key), sizeof(probe.key));
    HNode *popped = map.pop(&probe);
    assert(popped != nullptr);
    delete static_cast<TestNode *>(popped);

    assert(map.size() == 0);
    assert(find(map, 7) == nullptr);

    printf("testDelete: OK\n");
}

static void testCollisionChaining() {
    HMap map(testEq, deleteTestNode);

    for (int i = 0; i < 4; i++) {
        auto *n = new TestNode();
        n->key = i;
        n->val = i * 10;
        n->hcode = 1;  // force all four into the same bucket
        map.insert(n);
    }
    assert(map.size() == 4);

    for (int i = 0; i < 4; i++) {
        TestNode probe{};
        probe.key = i;
        probe.hcode = 1;
        HNode *found = map.lookup(&probe);
        assert(found != nullptr);
        assert(static_cast<TestNode *>(found)->val == i * 10);
    }

    printf("testCollisionChaining: OK\n");
}

static constexpr int kRehashKeys = 5000;

static void testProgressiveRehash() {
    HMap map(testEq, deleteTestNode);

    for (int i = 0; i < kRehashKeys; i++) {
        map.insert(makeNode(i, i));
    }
    assert(map.size() == static_cast<size_t>(kRehashKeys));

    for (int i = 0; i < kRehashKeys; i++) {
        TestNode *found = find(map, i);
        assert(found != nullptr);
        assert(found->val == i);
    }
    assert(find(map, -1) == nullptr);
    assert(find(map, kRehashKeys) == nullptr);

    for (int i = 0; i < kRehashKeys; i += 2) {
        TestNode probe{};
        probe.key = i;
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(&probe.key), sizeof(probe.key));
        HNode *popped = map.pop(&probe);
        assert(popped != nullptr);
        delete static_cast<TestNode *>(popped);
    }
    assert(map.size() == static_cast<size_t>(kRehashKeys / 2));

    for (int i = 0; i < kRehashKeys; i++) {
        TestNode *found = find(map, i);
        if (i % 2 == 0) {
            assert(found == nullptr);
        } else {
            assert(found != nullptr);
            assert(found->val == i);
        }
    }

    printf("testProgressiveRehash: OK\n");
}

int main() {
    testInsertAndLookup();
    testDelete();
    testCollisionChaining();
    testProgressiveRehash();
    printf("All hashtable tests passed.\n");
    return 0;
}
```

- [ ] **Step 2: Update the Makefile's test-hashtable rule and confirm it fails to build**

In `Makefile`, replace the `$(BUILD_DIR)/test_hashtable` rule (only this
rule — leave every other rule in the file untouched for now):

```makefile
$(BUILD_DIR)/test_hashtable: $(TEST_DIR)/test_hashtable.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/hashtable.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_hashtable.cpp $(SRC_DIR)/hashtable.cpp
```

Also add these two lines near the top of the `Makefile`, directly below
the existing `CC`/`CFLAGS` lines (both toolchains coexist until Task 3
finishes converting every module):

```makefile
CXX := c++
CXXFLAGS := -std=c++17 -Wall -Wextra
```

Run: `make test-hashtable`
Expected: FAIL — `src/hashtable.h` and `src/hashtable.cpp` don't exist
yet (`src/hashtable.h` still has its old C content at this point, which
won't satisfy the new test's C++ usage, and `src/hashtable.cpp` doesn't
exist at all).

- [ ] **Step 3: Write the implementation**

Overwrite `src/hashtable.h`:

```cpp
#ifndef HASHTABLE_H
#define HASHTABLE_H

#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>

struct HNode {
    HNode *next = nullptr;
    uint64_t hcode = 0;
};

using EqFn = bool (*)(const HNode *a, const HNode *b);
using DeleteFn = std::function<void(HNode *)>;

class HMap {
public:
    HMap(EqFn eq, DeleteFn deleter);
    ~HMap();

    HMap(const HMap &) = delete;
    HMap &operator=(const HMap &) = delete;

    void insert(HNode *node);
    HNode *lookup(const HNode *key) const;
    HNode *pop(const HNode *key);
    size_t size() const;

private:
    struct HTab {
        std::vector<HNode *> tab;
        size_t mask = 0;
        size_t size = 0;
    };

    static void htabInsert(HTab &htab, HNode *node);
    static HNode **htabLookup(HTab &htab, const HNode *key, EqFn eq);
    static HNode *htabDetach(HTab &htab, HNode **from);
    static void htabInit(HTab &htab, size_t n);

    void startResizing();
    void helpRehashing();

    EqFn eq_;
    DeleteFn deleter_;
    HTab newer_;
    HTab older_;
    size_t migratePos_ = 0;
};

uint64_t hashBytes(const uint8_t *data, size_t len);

#endif
```

Create `src/hashtable.cpp`:

```cpp
#include "hashtable.h"

#include <cassert>

namespace {
constexpr size_t kInitSize = 4;
constexpr size_t kMaxLoadFactor = 8;
constexpr size_t kRehashWork = 128;
}  // namespace

void HMap::htabInit(HTab &htab, size_t n) {
    assert(n > 0 && ((n - 1) & n) == 0);  // n must be a power of two
    htab.tab.assign(n, nullptr);
    htab.mask = n - 1;
    htab.size = 0;
}

void HMap::htabInsert(HTab &htab, HNode *node) {
    size_t pos = node->hcode & htab.mask;
    node->next = htab.tab[pos];
    htab.tab[pos] = node;
    htab.size++;
}

HNode **HMap::htabLookup(HTab &htab, const HNode *key, EqFn eq) {
    if (htab.tab.empty()) {
        return nullptr;
    }
    size_t pos = key->hcode & htab.mask;
    HNode **from = &htab.tab[pos];
    for (HNode *cur; (cur = *from) != nullptr; from = &cur->next) {
        if (cur->hcode == key->hcode && eq(cur, key)) {
            return from;
        }
    }
    return nullptr;
}

HNode *HMap::htabDetach(HTab &htab, HNode **from) {
    HNode *node = *from;
    *from = node->next;
    htab.size--;
    return node;
}

void HMap::startResizing() {
    assert(older_.tab.empty());
    older_ = std::move(newer_);
    htabInit(newer_, (older_.mask + 1) * 2);
    migratePos_ = 0;
}

void HMap::helpRehashing() {
    size_t nwork = 0;
    while (nwork < kRehashWork && older_.size > 0) {
        HNode **from = &older_.tab[migratePos_];
        if (!*from) {
            migratePos_++;
            continue;
        }
        htabInsert(newer_, htabDetach(older_, from));
        nwork++;
    }
    if (older_.size == 0 && !older_.tab.empty()) {
        older_ = HTab{};
    }
}

HMap::HMap(EqFn eq, DeleteFn deleter) : eq_(eq), deleter_(std::move(deleter)) {}

HMap::~HMap() {
    for (size_t i = 0; i < newer_.tab.size(); i++) {
        for (HNode *node = newer_.tab[i]; node;) {
            HNode *next = node->next;
            if (deleter_) {
                deleter_(node);
            }
            node = next;
        }
    }
    for (size_t i = 0; i < older_.tab.size(); i++) {
        for (HNode *node = older_.tab[i]; node;) {
            HNode *next = node->next;
            if (deleter_) {
                deleter_(node);
            }
            node = next;
        }
    }
}

void HMap::insert(HNode *node) {
    if (newer_.tab.empty()) {
        htabInit(newer_, kInitSize);
    }
    htabInsert(newer_, node);

    if (older_.tab.empty()) {
        size_t threshold = (newer_.mask + 1) * kMaxLoadFactor;
        if (newer_.size >= threshold) {
            startResizing();
        }
    }
    helpRehashing();
}

HNode *HMap::lookup(const HNode *key) const {
    auto *self = const_cast<HMap *>(this);
    HNode **from = htabLookup(self->newer_, key, eq_);
    if (!from) {
        from = htabLookup(self->older_, key, eq_);
    }
    return from ? *from : nullptr;
}

HNode *HMap::pop(const HNode *key) {
    HNode **from = htabLookup(newer_, key, eq_);
    if (from) {
        HNode *node = htabDetach(newer_, from);
        helpRehashing();
        return node;
    }
    from = htabLookup(older_, key, eq_);
    if (from) {
        HNode *node = htabDetach(older_, from);
        helpRehashing();
        return node;
    }
    return nullptr;
}

size_t HMap::size() const {
    return newer_.size + older_.size;
}

uint64_t hashBytes(const uint8_t *data, size_t len) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (size_t i = 0; i < len; i++) {
        h ^= data[i];
        h *= 0x100000001b3ULL;
    }
    return h;
}
```

Note on `lookup`'s `const_cast`: `lookup()` is logically const (it
doesn't mutate the map), but its private helper `htabLookup` returns a
mutable `HNode**` so `pop()` can reuse it to detach a node. The
`const_cast` here is safe and standard practice — `lookup()` itself never
writes through the returned slot address, it only dereferences it once to
return the node pointer.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `make test-hashtable`
Expected:
```
testInsertAndLookup: OK
testDelete: OK
testCollisionChaining: OK
testProgressiveRehash: OK
All hashtable tests passed.
```

Do **not** run `make all`, `make test`, or `make test-integration` — they
are expected to fail at this point (see Global Constraints).

- [ ] **Step 5: Commit**

```bash
git add Makefile src/hashtable.h src/hashtable.cpp test/test_hashtable.cpp
git rm src/hashtable.c test/test_hashtable.c
git commit -m "Convert hashtable module to idiomatic C++"
```

---

## Task 2: Protocol module

**Files:**
- Delete: `src/protocol.c`, `test/test_protocol.c`
- Modify: `src/protocol.h` (full rewrite), `Makefile` (test-protocol rule
  only)
- Create: `src/protocol.cpp`, `test/test_protocol.cpp`

**Interfaces:**
- Consumes: nothing from Task 1 (independent module).
- Produces (used by Task 3's `server.cpp`/`client.cpp` and Task 4's
  `bench/loadtest.cpp`):
  - `constexpr size_t K_MAX_MSG = 4096;`
  - `constexpr uint16_t SERVER_PORT = 1234;`
  - `enum class ResponseStatus : uint8_t { Ok = 0, Err = 1, Nx = 2 };`
  - `class Buffer` — `void append(const uint8_t *data, size_t len)`;
    `void append(std::string_view s)`; `void consume(size_t n)`;
    `const uint8_t *data() const`; `size_t size() const`;
    `bool empty() const`.
  - `bool encodeRequest(Buffer &out, const std::vector<std::string> &args);`
    (false if the encoded message would exceed `K_MAX_MSG`)
  - `std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len);`
  - `void encodeResponse(Buffer &out, ResponseStatus status, std::string_view data = {});`
  - `struct Response { ResponseStatus status; std::string data; };`
  - `std::optional<Response> parseResponse(const uint8_t *data, size_t len);`
  - `enum class FrameStatus { Incomplete, Malformed, Complete };`
  - `struct FrameInfo { size_t frameLen; size_t payloadOff; size_t payloadLen; };`
  - `FrameStatus tryParseFrame(const uint8_t *buf, size_t bufLen, FrameInfo &out);`
    (payload starts at `buf + out.payloadOff`, which is always 4)
  - `bool readFull(int fd, uint8_t *buf, size_t n);`
  - `bool writeAll(int fd, const uint8_t *buf, size_t n);`
  - `std::optional<Buffer> readFrame(int fd);` (result includes the
    4-byte header — payload is `result->data() + 4`,
    `result->size() - 4`)
  - `bool writeFrame(int fd, const uint8_t *payload, size_t len);`

- [ ] **Step 1: Delete the old C files and write the failing C++ test**

```bash
rm src/protocol.c test/test_protocol.c
```

Create `test/test_protocol.cpp`:

```cpp
#include <cassert>
#include <cstdio>
#include <cstring>
#include <sys/socket.h>
#include <unistd.h>
#include "../src/protocol.h"

static void testBufferAppendGrows() {
    Buffer buf;
    for (int i = 0; i < 1000; i++) {
        uint8_t b = static_cast<uint8_t>(i);
        buf.append(&b, 1);
    }
    assert(buf.size() == 1000);
    for (int i = 0; i < 1000; i++) {
        assert(buf.data()[i] == static_cast<uint8_t>(i));
    }
    printf("testBufferAppendGrows: OK\n");
}

static void testBufferConsume() {
    Buffer buf;
    buf.append(std::string_view("hello world"));
    buf.consume(6);
    assert(buf.size() == 5);
    assert(std::memcmp(buf.data(), "world", 5) == 0);
    printf("testBufferConsume: OK\n");
}

static void testRequestRoundtrip() {
    std::vector<std::string> args = {"set", "foo", "bar"};

    Buffer out;
    assert(encodeRequest(out, args));

    auto parsed = parseRequest(out.data(), out.size());
    assert(parsed.has_value());
    assert(parsed->size() == 3);
    assert((*parsed)[0] == "set");
    assert((*parsed)[1] == "foo");
    assert((*parsed)[2] == "bar");

    printf("testRequestRoundtrip: OK\n");
}

static void testRequestRejectsTruncated() {
    uint8_t bad[4];
    uint32_t n = 5;
    std::memcpy(bad, &n, 4);
    auto parsed = parseRequest(bad, 4);
    assert(!parsed.has_value());
    printf("testRequestRejectsTruncated: OK\n");
}

static void testResponseRoundtripWithData() {
    Buffer out;
    encodeResponse(out, ResponseStatus::Ok, "bar");

    auto resp = parseResponse(out.data(), out.size());
    assert(resp.has_value());
    assert(resp->status == ResponseStatus::Ok);
    assert(resp->data == "bar");

    printf("testResponseRoundtripWithData: OK\n");
}

static void testResponseRoundtripStatusOnly() {
    Buffer out;
    encodeResponse(out, ResponseStatus::Nx);

    auto resp = parseResponse(out.data(), out.size());
    assert(resp.has_value());
    assert(resp->status == ResponseStatus::Nx);
    assert(resp->data.empty());

    printf("testResponseRoundtripStatusOnly: OK\n");
}

static void testTryParseFrame() {
    Buffer payload;
    encodeResponse(payload, ResponseStatus::Ok, "hi");

    Buffer framed;
    uint32_t l = static_cast<uint32_t>(payload.size());
    framed.append(reinterpret_cast<uint8_t *>(&l), 4);
    framed.append(payload.data(), payload.size());

    FrameInfo info{};
    assert(tryParseFrame(framed.data(), 4, info) == FrameStatus::Incomplete);
    assert(tryParseFrame(framed.data(), 4 + payload.size() - 1, info) == FrameStatus::Incomplete);

    FrameStatus rv = tryParseFrame(framed.data(), framed.size(), info);
    assert(rv == FrameStatus::Complete);
    assert(info.frameLen == framed.size());
    assert(info.payloadLen == payload.size());
    assert(info.payloadOff == 4);

    printf("testTryParseFrame: OK\n");
}

static void testTryParseFrameRejectsOversized() {
    uint8_t buf[4];
    uint32_t huge = K_MAX_MSG + 1;
    std::memcpy(buf, &huge, 4);
    FrameInfo info{};
    assert(tryParseFrame(buf, 4, info) == FrameStatus::Malformed);
    printf("testTryParseFrameRejectsOversized: OK\n");
}

static void testFrameIoOverSocketpair() {
    int fds[2];
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, fds) == 0);

    assert(writeFrame(fds[0], reinterpret_cast<const uint8_t *>("ping"), 4));

    auto got = readFrame(fds[1]);
    assert(got.has_value());
    assert(got->size() == 4 + 4);
    assert(std::memcmp(got->data() + 4, "ping", 4) == 0);

    close(fds[0]);
    close(fds[1]);
    printf("testFrameIoOverSocketpair: OK\n");
}

int main() {
    testBufferAppendGrows();
    testBufferConsume();
    testRequestRoundtrip();
    testRequestRejectsTruncated();
    testResponseRoundtripWithData();
    testResponseRoundtripStatusOnly();
    testTryParseFrame();
    testTryParseFrameRejectsOversized();
    testFrameIoOverSocketpair();
    printf("All protocol tests passed.\n");
    return 0;
}
```

- [ ] **Step 2: Update the Makefile's test-protocol rule and confirm it fails to build**

In `Makefile`, replace the `$(BUILD_DIR)/test_protocol` rule (only this
rule — leave `all`, `server`, `client`, `server_asan`, `client_asan`
untouched, they are already broken from Task 1 and stay that way until
Task 3):

```makefile
$(BUILD_DIR)/test_protocol: $(TEST_DIR)/test_protocol.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_protocol.cpp $(SRC_DIR)/protocol.cpp
```

Run: `make test-protocol`
Expected: FAIL — `src/protocol.cpp` doesn't exist yet and `src/protocol.h`
still has its old C content.

- [ ] **Step 3: Write the implementation**

Overwrite `src/protocol.h`:

```cpp
#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

constexpr size_t K_MAX_MSG = 4096;
constexpr uint16_t SERVER_PORT = 1234;

enum class ResponseStatus : uint8_t {
    Ok = 0,
    Err = 1,
    Nx = 2,
};

class Buffer {
public:
    void append(const uint8_t *data, size_t len);
    void append(std::string_view s);
    void consume(size_t n);

    const uint8_t *data() const { return buf_.data(); }
    size_t size() const { return buf_.size(); }
    bool empty() const { return buf_.empty(); }

private:
    std::vector<uint8_t> buf_;
};

bool encodeRequest(Buffer &out, const std::vector<std::string> &args);
std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len);

void encodeResponse(Buffer &out, ResponseStatus status, std::string_view data = {});

struct Response {
    ResponseStatus status;
    std::string data;
};
std::optional<Response> parseResponse(const uint8_t *data, size_t len);

enum class FrameStatus {
    Incomplete,
    Malformed,
    Complete,
};

struct FrameInfo {
    size_t frameLen;
    size_t payloadOff;
    size_t payloadLen;
};

FrameStatus tryParseFrame(const uint8_t *buf, size_t bufLen, FrameInfo &out);

bool readFull(int fd, uint8_t *buf, size_t n);
bool writeAll(int fd, const uint8_t *buf, size_t n);
std::optional<Buffer> readFrame(int fd);
bool writeFrame(int fd, const uint8_t *payload, size_t len);

#endif
```

Create `src/protocol.cpp`:

```cpp
#include "protocol.h"

#include <cstring>
#include <unistd.h>

void Buffer::append(const uint8_t *data, size_t len) {
    buf_.insert(buf_.end(), data, data + len);
}

void Buffer::append(std::string_view s) {
    append(reinterpret_cast<const uint8_t *>(s.data()), s.size());
}

void Buffer::consume(size_t n) {
    buf_.erase(buf_.begin(), buf_.begin() + static_cast<long>(n));
}

bool encodeRequest(Buffer &out, const std::vector<std::string> &args) {
    uint32_t n = static_cast<uint32_t>(args.size());
    out.append(reinterpret_cast<const uint8_t *>(&n), 4);
    for (const auto &arg : args) {
        uint32_t l = static_cast<uint32_t>(arg.size());
        out.append(reinterpret_cast<const uint8_t *>(&l), 4);
        out.append(arg);
    }
    return out.size() <= K_MAX_MSG;
}

std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len) {
    if (len < 4) {
        return std::nullopt;
    }
    uint32_t nargs;
    std::memcpy(&nargs, data, 4);
    if (nargs > 1024) {
        return std::nullopt;
    }

    size_t pos = 4;
    std::vector<std::string> args;
    args.reserve(nargs);
    for (uint32_t i = 0; i < nargs; i++) {
        if (pos + 4 > len) {
            return std::nullopt;
        }
        uint32_t l;
        std::memcpy(&l, data + pos, 4);
        pos += 4;
        if (pos + l > len) {
            return std::nullopt;
        }
        args.emplace_back(reinterpret_cast<const char *>(data + pos), l);
        pos += l;
    }
    if (pos != len) {
        return std::nullopt;
    }
    return args;
}

void encodeResponse(Buffer &out, ResponseStatus status, std::string_view data) {
    uint8_t s = static_cast<uint8_t>(status);
    out.append(&s, 1);
    if (!data.empty()) {
        uint32_t l = static_cast<uint32_t>(data.size());
        out.append(reinterpret_cast<const uint8_t *>(&l), 4);
        out.append(data);
    }
}

std::optional<Response> parseResponse(const uint8_t *data, size_t len) {
    if (len < 1) {
        return std::nullopt;
    }
    ResponseStatus status = static_cast<ResponseStatus>(data[0]);
    if (len == 1) {
        return Response{status, std::string()};
    }
    if (len < 5) {
        return std::nullopt;
    }
    uint32_t l;
    std::memcpy(&l, data + 1, 4);
    if (5 + static_cast<size_t>(l) != len) {
        return std::nullopt;
    }
    return Response{status, std::string(reinterpret_cast<const char *>(data + 5), l)};
}

FrameStatus tryParseFrame(const uint8_t *buf, size_t bufLen, FrameInfo &out) {
    if (bufLen < 4) {
        return FrameStatus::Incomplete;
    }
    uint32_t len;
    std::memcpy(&len, buf, 4);
    if (len > K_MAX_MSG) {
        return FrameStatus::Malformed;
    }
    if (bufLen < 4 + static_cast<size_t>(len)) {
        return FrameStatus::Incomplete;
    }
    out.frameLen = 4 + len;
    out.payloadOff = 4;
    out.payloadLen = len;
    return FrameStatus::Complete;
}

bool readFull(int fd, uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = read(fd, buf, n);
        if (rv <= 0) {
            return false;
        }
        n -= static_cast<size_t>(rv);
        buf += rv;
    }
    return true;
}

bool writeAll(int fd, const uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = write(fd, buf, n);
        if (rv <= 0) {
            return false;
        }
        n -= static_cast<size_t>(rv);
        buf += rv;
    }
    return true;
}

std::optional<Buffer> readFrame(int fd) {
    uint8_t head[4];
    if (!readFull(fd, head, 4)) {
        return std::nullopt;
    }
    uint32_t len;
    std::memcpy(&len, head, 4);
    if (len > K_MAX_MSG) {
        return std::nullopt;
    }

    Buffer out;
    out.append(head, 4);
    if (len > 0) {
        std::vector<uint8_t> tmp(len);
        if (!readFull(fd, tmp.data(), len)) {
            return std::nullopt;
        }
        out.append(tmp.data(), len);
    }
    return out;
}

bool writeFrame(int fd, const uint8_t *payload, size_t len) {
    if (len > K_MAX_MSG) {
        return false;
    }
    uint8_t head[4];
    uint32_t l = static_cast<uint32_t>(len);
    std::memcpy(head, &l, 4);
    if (!writeAll(fd, head, 4)) {
        return false;
    }
    if (len > 0 && !writeAll(fd, payload, len)) {
        return false;
    }
    return true;
}
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `make test-protocol`
Expected:
```
testBufferAppendGrows: OK
testBufferConsume: OK
testRequestRoundtrip: OK
testRequestRejectsTruncated: OK
testResponseRoundtripWithData: OK
testResponseRoundtripStatusOnly: OK
testTryParseFrame: OK
testTryParseFrameRejectsOversized: OK
testFrameIoOverSocketpair: OK
All protocol tests passed.
```

Do **not** run `make all`, `make test`, or `make test-integration` — same
caveat as Task 1, now compounded (`protocol.c` is also gone). Task 3
restores full parity.

- [ ] **Step 5: Commit**

```bash
git add Makefile src/protocol.h src/protocol.cpp test/test_protocol.cpp
git rm src/protocol.c test/test_protocol.c
git commit -m "Convert protocol module to idiomatic C++"
```

---

## Task 3: Server and client, and full Makefile restoration

**Files:**
- Delete: `src/server.c`, `src/client.c`
- Modify: `Makefile` (all remaining rules: `CC`/`CFLAGS` removed, `all`,
  `server`, `client`, `server_asan`, `client_asan` all switched to
  `$(CXX)`/`.cpp`)
- Create: `src/server.cpp`, `src/client.cpp`

**Interfaces:**
- Consumes: Task 1's `HNode`/`HMap`/`hashBytes` (exact signatures above)
  and Task 2's `Buffer`/`encodeRequest`/`parseRequest`/`encodeResponse`/
  `parseResponse`/`tryParseFrame`/`readFrame`/`writeFrame`/`SERVER_PORT`/
  `K_MAX_MSG`/`ResponseStatus` (exact signatures above). Do not modify
  `hashtable.{h,cpp}` or `protocol.{h,cpp}`.
- Produces: `build/server` (listens on `127.0.0.1:1234`), `build/client`
  (`./build/client <cmd> [args...]`, prints the value / `OK` / `(nil)` /
  `(error) ...`).

- [ ] **Step 1: Delete the old C files and write `src/server.cpp`**

```bash
rm src/server.c src/client.c
```

Create `src/server.cpp`:

```cpp
#include <cerrno>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <memory>
#include <vector>

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>

#include "hashtable.h"
#include "protocol.h"

class Entry : public HNode {
public:
    std::string key;
    std::string val;
};

static bool entryEq(const HNode *lhs, const HNode *rhs) {
    const auto *le = static_cast<const Entry *>(lhs);
    const auto *re = static_cast<const Entry *>(rhs);
    return le->key == re->key;
}

class KvStore {
public:
    KvStore() : map_(entryEq, [](HNode *n) { delete static_cast<Entry *>(n); }) {}

    std::optional<std::string> get(std::string_view key) const {
        Entry probe;
        probe.key = std::string(key);
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(probe.key.data()), probe.key.size());

        HNode *node = map_.lookup(&probe);
        if (!node) {
            return std::nullopt;
        }
        return static_cast<Entry *>(node)->val;
    }

    void set(std::string_view key, std::string_view val) {
        Entry probe;
        probe.key = std::string(key);
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(probe.key.data()), probe.key.size());

        HNode *node = map_.lookup(&probe);
        if (node) {
            static_cast<Entry *>(node)->val = std::string(val);
            return;
        }
        auto *e = new Entry();
        e->key = std::string(key);
        e->val = std::string(val);
        e->hcode = probe.hcode;
        map_.insert(e);
    }

    bool del(std::string_view key) {
        Entry probe;
        probe.key = std::string(key);
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(probe.key.data()), probe.key.size());

        HNode *node = map_.pop(&probe);
        if (!node) {
            return false;
        }
        delete static_cast<Entry *>(node);
        return true;
    }

private:
    HMap map_;
};

class Conn {
public:
    explicit Conn(int fd) : fd_(fd) {
        int flags = fcntl(fd_, F_GETFL, 0);
        if (flags == -1) {
            perror("fcntl(F_GETFL)");
            exit(1);
        }
        if (fcntl(fd_, F_SETFL, flags | O_NONBLOCK) == -1) {
            perror("fcntl(F_SETFL)");
            exit(1);
        }
    }

    ~Conn() { close(fd_); }

    Conn(const Conn &) = delete;
    Conn &operator=(const Conn &) = delete;

    int fd() const { return fd_; }

    bool wantRead = true;
    bool wantWrite = false;
    bool wantClose = false;
    Buffer incoming;
    Buffer outgoing;

private:
    int fd_;
};

static std::vector<std::unique_ptr<Conn>> g_fd2conn;

static void fd2connPut(int fd, std::unique_ptr<Conn> conn) {
    if (static_cast<size_t>(fd) >= g_fd2conn.size()) {
        g_fd2conn.resize(static_cast<size_t>(fd) + 1);
    }
    g_fd2conn[static_cast<size_t>(fd)] = std::move(conn);
}

static void encodeCommand(KvStore &store, const std::vector<std::string> &args, Buffer &out) {
    if (args.size() == 2 && args[0] == "get") {
        auto val = store.get(args[1]);
        if (!val) {
            encodeResponse(out, ResponseStatus::Nx);
        } else {
            encodeResponse(out, ResponseStatus::Ok, *val);
        }
    } else if (args.size() == 3 && args[0] == "set") {
        store.set(args[1], args[2]);
        encodeResponse(out, ResponseStatus::Ok);
    } else if (args.size() == 2 && args[0] == "del") {
        bool existed = store.del(args[1]);
        encodeResponse(out, existed ? ResponseStatus::Ok : ResponseStatus::Nx);
    } else {
        encodeResponse(out, ResponseStatus::Err);
    }
}

static void doRequest(KvStore &store, const std::vector<std::string> &args, Buffer &out) {
    // Responses are framed just like requests: build the payload into a
    // scratch buffer, then prepend its 4-byte length before appending to
    // the connection's real outgoing buffer.
    Buffer resp;
    encodeCommand(store, args, resp);

    uint32_t len = static_cast<uint32_t>(resp.size());
    out.append(reinterpret_cast<const uint8_t *>(&len), 4);
    out.append(resp.data(), resp.size());
}

static void processBufferedRequests(KvStore &store, Conn &conn) {
    while (true) {
        FrameInfo info{};
        FrameStatus status = tryParseFrame(conn.incoming.data(), conn.incoming.size(), info);
        if (status == FrameStatus::Incomplete) {
            break;
        }
        if (status == FrameStatus::Malformed) {
            conn.wantClose = true;
            return;
        }
        auto args = parseRequest(conn.incoming.data() + info.payloadOff, info.payloadLen);
        if (!args) {
            conn.wantClose = true;
            return;
        }
        doRequest(store, *args, conn.outgoing);
        conn.incoming.consume(info.frameLen);
    }
}

static void handleRead(KvStore &store, Conn &conn) {
    uint8_t tmp[64 * 1024];
    ssize_t rv = read(conn.fd(), tmp, sizeof(tmp));
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv <= 0) {
        conn.wantClose = true;
        return;
    }
    conn.incoming.append(tmp, static_cast<size_t>(rv));
    processBufferedRequests(store, conn);
    conn.wantWrite = conn.outgoing.size() > 0;
}

static void handleWrite(Conn &conn) {
    ssize_t rv = write(conn.fd(), conn.outgoing.data(), conn.outgoing.size());
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv < 0) {
        conn.wantClose = true;
        return;
    }
    conn.outgoing.consume(static_cast<size_t>(rv));
    conn.wantWrite = conn.outgoing.size() > 0;
}

static int makeListener() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket()");
        exit(1);
    }

    int val = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &val, sizeof(val));

    struct sockaddr_in addr {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(fd, reinterpret_cast<struct sockaddr *>(&addr), sizeof(addr)) != 0) {
        perror("bind()");
        exit(1);
    }
    if (listen(fd, SOMAXCONN) != 0) {
        perror("listen()");
        exit(1);
    }

    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
    return fd;
}

static void acceptNewConn(int listenFd) {
    struct sockaddr_in clientAddr {};
    socklen_t addrlen = sizeof(clientAddr);
    int connfd = accept(listenFd, reinterpret_cast<struct sockaddr *>(&clientAddr), &addrlen);
    if (connfd < 0) {
        return;
    }
    fd2connPut(connfd, std::make_unique<Conn>(connfd));
}

int main() {
    signal(SIGPIPE, SIG_IGN);
    KvStore store;

    int listenFd = makeListener();
    fprintf(stderr, "listening on 127.0.0.1:%d\n", SERVER_PORT);

    std::vector<struct pollfd> pollArgs;

    while (true) {
        pollArgs.clear();
        pollArgs.push_back({listenFd, POLLIN, 0});

        for (auto &conn : g_fd2conn) {
            if (!conn) {
                continue;
            }
            struct pollfd pfd {};
            pfd.fd = conn->fd();
            pfd.events = POLLERR;
            if (conn->wantRead) {
                pfd.events |= POLLIN;
            }
            if (conn->wantWrite) {
                pfd.events |= POLLOUT;
            }
            pollArgs.push_back(pfd);
        }

        int rv = poll(pollArgs.data(), static_cast<nfds_t>(pollArgs.size()), -1);
        if (rv < 0 && errno == EINTR) {
            continue;
        }
        if (rv < 0) {
            perror("poll()");
            exit(1);
        }

        if (pollArgs[0].revents & POLLIN) {
            acceptNewConn(listenFd);
        }

        for (size_t i = 1; i < pollArgs.size(); i++) {
            short re = pollArgs[i].revents;
            if (!re) {
                continue;
            }
            int fd = pollArgs[i].fd;
            Conn *conn = g_fd2conn[static_cast<size_t>(fd)].get();
            if (!conn) {
                continue;
            }
            if (re & POLLIN) {
                handleRead(store, *conn);
            }
            if (!conn->wantClose && (re & POLLOUT)) {
                handleWrite(*conn);
            }
            if (conn->wantClose || (re & (POLLERR | POLLHUP))) {
                g_fd2conn[static_cast<size_t>(fd)].reset();
            }
        }
    }

    return 0;
}
```

- [ ] **Step 2: Write `src/client.cpp`**

```cpp
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include "protocol.h"

static int connectToServer() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket()");
        exit(1);
    }

    struct sockaddr_in addr {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    if (connect(fd, reinterpret_cast<struct sockaddr *>(&addr), sizeof(addr)) != 0) {
        perror("connect()");
        exit(1);
    }
    return fd;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        std::cerr << "usage: " << argv[0] << " <cmd> [args...]\n";
        return 1;
    }

    std::vector<std::string> args(argv + 1, argv + argc);

    Buffer req;
    if (!encodeRequest(req, args)) {
        std::cerr << "request too large\n";
        return 1;
    }

    int fd = connectToServer();
    if (!writeFrame(fd, req.data(), req.size())) {
        std::cerr << "write_frame failed\n";
        return 1;
    }

    auto resp = readFrame(fd);
    if (!resp) {
        std::cerr << "read_frame failed\n";
        return 1;
    }

    auto parsed = parseResponse(resp->data() + 4, resp->size() - 4);
    if (!parsed) {
        std::cerr << "bad response\n";
        return 1;
    }

    switch (parsed->status) {
    case ResponseStatus::Ok:
        if (!parsed->data.empty()) {
            std::cout << parsed->data << "\n";
        } else {
            std::cout << "OK\n";
        }
        break;
    case ResponseStatus::Nx:
        std::cout << "(nil)\n";
        break;
    case ResponseStatus::Err:
        std::cout << "(error) unknown command or wrong number of arguments\n";
        break;
    }

    close(fd);
    return 0;
}
```

- [ ] **Step 3: Rewrite the Makefile in full, restoring every target**

Overwrite `Makefile`:

```makefile
CXX := c++
CXXFLAGS := -std=c++17 -Wall -Wextra
RELEASE_FLAGS := -O2
ASAN_FLAGS := -fsanitize=address -g

SRC_DIR := src
TEST_DIR := test
BUILD_DIR := build

.PHONY: all test clean test-hashtable test-protocol test-integration

all: $(BUILD_DIR)/server $(BUILD_DIR)/client

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/server: $(SRC_DIR)/server.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/hashtable.h $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/server.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/protocol.cpp

$(BUILD_DIR)/client: $(SRC_DIR)/client.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/client.cpp $(SRC_DIR)/protocol.cpp

$(BUILD_DIR)/server_asan: $(SRC_DIR)/server.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/hashtable.h $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(SRC_DIR)/server.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/protocol.cpp

$(BUILD_DIR)/client_asan: $(SRC_DIR)/client.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(SRC_DIR)/client.cpp $(SRC_DIR)/protocol.cpp

test: test-hashtable test-protocol test-integration

test-hashtable: $(BUILD_DIR)/test_hashtable
	$(BUILD_DIR)/test_hashtable

test-protocol: $(BUILD_DIR)/test_protocol
	$(BUILD_DIR)/test_protocol

test-integration: $(BUILD_DIR)/server_asan $(BUILD_DIR)/client_asan
	$(TEST_DIR)/test_integration.sh

$(BUILD_DIR)/test_hashtable: $(TEST_DIR)/test_hashtable.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/hashtable.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_hashtable.cpp $(SRC_DIR)/hashtable.cpp

$(BUILD_DIR)/test_protocol: $(TEST_DIR)/test_protocol.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_protocol.cpp $(SRC_DIR)/protocol.cpp

clean:
	rm -rf $(BUILD_DIR)
```

Run: `make clean && make all`
Expected: `build/server` and `build/client` compile with no warnings.

- [ ] **Step 4: Manually verify server + client end-to-end**

Run:
```bash
./build/server &
sleep 0.3
./build/client get foo
./build/client set foo bar
./build/client get foo
./build/client set foo baz
./build/client get foo
./build/client del foo
./build/client get foo
./build/client bogus a b c
kill %1
```

Expected output, in order:
```
(nil)
OK
bar
OK
baz
OK
(nil)
(error) unknown command or wrong number of arguments
```

- [ ] **Step 5: Run the full restored test suite**

Run: `make clean && make test`
Expected: hashtable tests pass, protocol tests pass, then the
integration test builds `server_asan`/`client_asan` and runs
`test/test_integration.sh` unmodified (it only shells out to binary
paths, so it needs no changes) — basic command checks, then ~10,000 keys
inserted to force a resize (this takes roughly a minute), then:
```
All integration tests passed.
```
with zero exit code and no AddressSanitizer output.

- [ ] **Step 6: Commit**

```bash
git add Makefile src/server.cpp src/client.cpp
git rm src/server.c src/client.c
git commit -m "Convert server and client to idiomatic C++, restore full Makefile"
```

---

## Task 4: Bench tool conversion and performance regression check

**Files:**
- Delete: `bench/loadtest.c` (untracked in git — plain file replacement,
  no `git rm` needed)
- Modify: `Makefile` (add `bench` target)
- Create: `bench/loadtest.cpp`

**Interfaces:**
- Consumes: Task 2's `Buffer`/`encodeRequest`/`writeFrame`/`readFrame`/
  `parseResponse`/`SERVER_PORT` (exact signatures above).
- Produces: `build/loadtest <n_clients> <duration_sec>` — same CLI and
  output format as the C version (`clients=... throughput=... ops/sec`,
  `latency_us: min=... p50=... p90=... p99=... max=... mean=...`).

- [ ] **Step 1: Delete the old file and write `bench/loadtest.cpp`**

```bash
rm bench/loadtest.c
```

Create `bench/loadtest.cpp`:

```cpp
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <unistd.h>

#include "../src/protocol.h"

using Clock = std::chrono::steady_clock;

struct ThreadResult {
    long opsDone = 0;
    std::vector<double> latenciesUs;
    bool connectFailed = false;
};

static int connectServer() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        return -1;
    }
    int one = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));

    struct sockaddr_in addr {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (connect(fd, reinterpret_cast<struct sockaddr *>(&addr), sizeof(addr)) != 0) {
        close(fd);
        return -1;
    }
    return fd;
}

static void worker(int threadId, double durationSec, ThreadResult &result) {
    int fd = connectServer();
    if (fd < 0) {
        result.connectFailed = true;
        return;
    }

    long counter = 0;
    auto tEnd = Clock::now() + std::chrono::duration_cast<Clock::duration>(
                                   std::chrono::duration<double>(durationSec));

    while (Clock::now() < tEnd) {
        bool isSet = (counter % 2 == 0);
        std::string key = "lt:" + std::to_string(threadId) + ":" + std::to_string(counter / 2);

        std::vector<std::string> args;
        if (isSet) {
            args = {"set", key, "v" + std::to_string(counter)};
        } else {
            args = {"get", key};
        }

        Buffer req;
        encodeRequest(req, args);

        auto t0 = Clock::now();
        if (!writeFrame(fd, req.data(), req.size())) {
            break;
        }
        auto resp = readFrame(fd);
        if (!resp) {
            break;
        }
        auto t1 = Clock::now();

        parseResponse(resp->data() + 4, resp->size() - 4);

        double us = std::chrono::duration<double, std::micro>(t1 - t0).count();
        result.latenciesUs.push_back(us);
        result.opsDone++;
        counter++;
    }

    close(fd);
}

int main(int argc, char **argv) {
    int nClients = argc > 1 ? std::atoi(argv[1]) : 200;
    double duration = argc > 2 ? std::atof(argv[2]) : 10.0;

    std::vector<std::thread> threads;
    std::vector<ThreadResult> results(static_cast<size_t>(nClients));

    auto tStart = Clock::now();
    for (int i = 0; i < nClients; i++) {
        threads.emplace_back(worker, i, duration, std::ref(results[static_cast<size_t>(i)]));
    }
    for (auto &t : threads) {
        t.join();
    }
    double elapsed = std::chrono::duration<double>(Clock::now() - tStart).count();

    long totalOps = 0;
    int failed = 0;
    std::vector<double> all;
    for (auto &r : results) {
        if (r.connectFailed) {
            failed++;
        }
        totalOps += r.opsDone;
        all.insert(all.end(), r.latenciesUs.begin(), r.latenciesUs.end());
    }

    printf("clients=%d duration_target=%.1fs actual_wall=%.3fs failed_connects=%d\n",
           nClients, duration, elapsed, failed);

    if (all.empty()) {
        printf("total_ops=0 (no successful requests)\n");
        return failed > 0 ? 1 : 0;
    }

    std::sort(all.begin(), all.end());
    double sum = 0;
    for (double v : all) {
        sum += v;
    }

    printf("total_ops=%ld throughput=%.1f ops/sec\n", totalOps, static_cast<double>(totalOps) / elapsed);
    printf("latency_us: min=%.1f p50=%.1f p90=%.1f p99=%.1f max=%.1f mean=%.1f\n",
           all.front(),
           all[all.size() * 50 / 100],
           all[all.size() * 90 / 100],
           all[all.size() * 99 / 100],
           all.back(),
           sum / static_cast<double>(all.size()));

    return 0;
}
```

- [ ] **Step 2: Add the bench target to the Makefile**

In `Makefile`, add a `BENCH_DIR` variable next to the existing `SRC_DIR`/
`TEST_DIR`/`BUILD_DIR` lines:

```makefile
BENCH_DIR := bench
```

Add `bench` to the `.PHONY` line (alongside the existing targets), and
add these two rules anywhere after the `client_asan` rule:

```makefile
bench: $(BUILD_DIR)/loadtest

$(BUILD_DIR)/loadtest: $(BENCH_DIR)/loadtest.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -pthread -o $@ $(BENCH_DIR)/loadtest.cpp $(SRC_DIR)/protocol.cpp
```

Run: `make bench`
Expected: `build/loadtest` compiles with no warnings.

- [ ] **Step 3: Run the performance regression check**

```bash
./build/server &
sleep 0.3
./build/loadtest 200 10
kill %1
```

Expected: no `failed_connects`, and throughput in the same ballpark as
the C baseline (~160,000 ops/sec, p50 latency ≈1.2ms at 200 concurrent
clients) — the hot path (hashtable, `poll()` loop) is algorithmically
identical to the C version, so a large regression (e.g. dropping below
~100,000 ops/sec) would indicate something was introduced in Task 3 (an
unnecessary copy, a lock, etc.) and should be investigated before
committing, not shrugged off.

- [ ] **Step 4: Re-run the full test suite one last time**

Run: `make clean && make test`
Expected: same as Task 3 Step 5 — all three suites pass, zero ASan
errors.

- [ ] **Step 5: Commit**

```bash
git add Makefile bench/loadtest.cpp
git commit -m "Convert load-test bench tool to C++; verify no performance regression"
```

---

## Final Verification

- [ ] Run `make clean && make all && make bench && make test` from the
  repo root — every target succeeds, no ASan errors.
- [ ] Confirm no `.c` files remain under `src/`, `test/`, or `bench/`
  (`find src test bench -name '*.c'` should print nothing).
- [ ] Manually run `./build/server &` and drive a few commands with
  `./build/client` to confirm the release binaries behave identically to
  the original C version's documented behavior.
- [ ] `./build/loadtest 200 10` throughput is within the expected range
  of the C baseline (no unexplained regression).
