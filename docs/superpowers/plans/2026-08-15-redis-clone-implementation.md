# Build Your Own Redis (Chapters 1-8) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working C key-value server + client matching where the
build-your-own.org/redis tutorial lands after chapter 8: a `poll()`-based
non-blocking TCP server exposing `get`/`set`/`del` over a custom
length-prefixed binary protocol, backed by a hand-rolled intrusive
chaining hashtable with progressive (incremental) rehashing.

**Architecture:** Two pure-logic modules (`hashtable.c`, `protocol.c`) with
no socket/IO dependencies, each unit-tested directly. `server.c` and
`client.c` are thin glue over those two modules plus POSIX sockets/poll,
verified end-to-end via a driven integration test. All test binaries build
with AddressSanitizer since this project hand-manages memory in C.

**Tech Stack:** C11, POSIX sockets (`socket`/`bind`/`listen`/`accept`),
`poll()`, GNU Make, bash (integration test only). No external dependencies.

## Global Constraints

- Language: C11, compiled with `cc`, no external libraries beyond POSIX libc.
- Platform: uses `poll()` (not `epoll`/`kqueue`) so it runs unmodified on macOS and Linux.
- Wire protocol: every message is `[4-byte little-endian length][payload]`, payload capped at `K_MAX_MSG = 4096` bytes.
- Request payload: `[4-byte nstr]{[4-byte len_i][len_i bytes]}*nstr`.
- Response payload: `[1-byte status][4-byte len][len bytes]` — the `len`/`string` are omitted entirely when there's no trailing data.
- Status codes are fixed: `RES_OK = 0`, `RES_ERR = 1`, `RES_NX = 2`.
- Server listens on `127.0.0.1:1234` (`SERVER_PORT` in `protocol.h`).
- Hashtable: intrusive chaining (`HNode` embedded as the struct's first field), power-of-two bucket counts, resize triggered at load factor 8, progressive rehashing moving 128 entries per helper call, hash function is FNV-1a (`hash_bytes`).
- Not RESP-compatible; `redis-cli` will not work against this server — use the project's own `client` binary.
- Out of scope (chapters 9+): serialization, AVL trees, sorted sets, timers/TTL, thread pool, persistence, replication, auth.
- No `-DNDEBUG` in any build — unit tests rely on `assert()` to signal failure.
- Test binaries (unit and integration) are built with `-fsanitize=address`; this is the primary correctness net for the hand-rolled `malloc`/`free` in the hashtable and protocol code.

---

## Task 1: Hashtable module

**Files:**
- Create: `Makefile`
- Create: `.gitignore`
- Create: `src/hashtable.h`
- Create: `src/hashtable.c`
- Test: `test/test_hashtable.c`

**Interfaces:**
- Produces (used by Task 3's `server.c` and by `test/test_hashtable.c`):
  - `typedef struct HNode { struct HNode *next; uint64_t hcode; } HNode;`
  - `typedef struct { HNode **tab; size_t mask; size_t size; } HTab;`
  - `typedef struct { HTab newer; HTab older; size_t migrate_pos; } HMap;`
  - `typedef bool (*HEqFn)(HNode *node, HNode *key);`
  - `void hm_init(HMap *map);`
  - `void hm_insert(HMap *map, HNode *node);`
  - `HNode *hm_lookup(HMap *map, HNode *key, HEqFn eq);`
  - `HNode *hm_pop(HMap *map, HNode *key, HEqFn eq);`
  - `size_t hm_size(const HMap *map);`
  - `void hm_destroy(HMap *map, void (*free_node)(HNode *node));`
  - `uint64_t hash_bytes(const uint8_t *data, size_t len);`
- Consumes: nothing (this module has no dependencies beyond libc).

- [ ] **Step 1: Write the failing test**

Create `test/test_hashtable.c`:

```c
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/hashtable.h"

typedef struct {
    HNode node;
    int key;
    int val;
} TestNode;

static bool test_eq(HNode *a, HNode *b) {
    return ((TestNode *)a)->key == ((TestNode *)b)->key;
}

static TestNode *make_node(int key, int val) {
    TestNode *n = malloc(sizeof(TestNode));
    n->node.next = NULL;
    n->node.hcode = hash_bytes((const uint8_t *)&key, sizeof(key));
    n->key = key;
    n->val = val;
    return n;
}

static TestNode *find(HMap *map, int key) {
    TestNode probe = {0};
    probe.key = key;
    probe.node.hcode = hash_bytes((const uint8_t *)&key, sizeof(key));
    HNode *found = hm_lookup(map, &probe.node, test_eq);
    return found ? (TestNode *)found : NULL;
}

static void free_node_cb(HNode *node) {
    free(node);
}

static void test_insert_and_lookup(void) {
    HMap map;
    hm_init(&map);

    TestNode *n = make_node(42, 100);
    hm_insert(&map, &n->node);

    TestNode *found = find(&map, 42);
    assert(found != NULL);
    assert(found->val == 100);
    assert(find(&map, 99) == NULL);

    hm_destroy(&map, free_node_cb);
    printf("test_insert_and_lookup: OK\n");
}

static void test_delete(void) {
    HMap map;
    hm_init(&map);

    TestNode *n = make_node(7, 77);
    hm_insert(&map, &n->node);
    assert(hm_size(&map) == 1);

    TestNode probe = {0};
    probe.key = 7;
    probe.node.hcode = hash_bytes((const uint8_t *)&probe.key, sizeof(probe.key));
    HNode *popped = hm_pop(&map, &probe.node, test_eq);
    assert(popped != NULL);
    free(popped);

    assert(hm_size(&map) == 0);
    assert(find(&map, 7) == NULL);

    hm_destroy(&map, free_node_cb);
    printf("test_delete: OK\n");
}

static void test_collision_chaining(void) {
    HMap map;
    hm_init(&map);

    /* Force all four nodes into the same bucket by giving them an
       identical hash code, regardless of table size. */
    for (int i = 0; i < 4; i++) {
        TestNode *n = malloc(sizeof(TestNode));
        n->node.next = NULL;
        n->node.hcode = 1;
        n->key = i;
        n->val = i * 10;
        hm_insert(&map, &n->node);
    }
    assert(hm_size(&map) == 4);

    for (int i = 0; i < 4; i++) {
        TestNode probe = {0};
        probe.key = i;
        probe.node.hcode = 1;
        HNode *found = hm_lookup(&map, &probe.node, test_eq);
        assert(found != NULL);
        assert(((TestNode *)found)->val == i * 10);
    }

    hm_destroy(&map, free_node_cb);
    printf("test_collision_chaining: OK\n");
}

#define N_REHASH_KEYS 5000

static void test_progressive_rehash(void) {
    HMap map;
    hm_init(&map);

    for (int i = 0; i < N_REHASH_KEYS; i++) {
        hm_insert(&map, &make_node(i, i)->node);
    }
    assert(hm_size(&map) == N_REHASH_KEYS);

    for (int i = 0; i < N_REHASH_KEYS; i++) {
        TestNode *found = find(&map, i);
        assert(found != NULL);
        assert(found->val == i);
    }
    assert(find(&map, -1) == NULL);
    assert(find(&map, N_REHASH_KEYS) == NULL);

    /* Delete every other key while a rehash may still be migrating in the
       background, then confirm the rest still resolve correctly. */
    for (int i = 0; i < N_REHASH_KEYS; i += 2) {
        TestNode probe = {0};
        probe.key = i;
        probe.node.hcode = hash_bytes((const uint8_t *)&probe.key, sizeof(probe.key));
        HNode *popped = hm_pop(&map, &probe.node, test_eq);
        assert(popped != NULL);
        free(popped);
    }
    assert(hm_size(&map) == N_REHASH_KEYS / 2);

    for (int i = 0; i < N_REHASH_KEYS; i++) {
        TestNode *found = find(&map, i);
        if (i % 2 == 0) {
            assert(found == NULL);
        } else {
            assert(found != NULL);
            assert(found->val == i);
        }
    }

    hm_destroy(&map, free_node_cb);
    printf("test_progressive_rehash: OK\n");
}

int main(void) {
    test_insert_and_lookup();
    test_delete();
    test_collision_chaining();
    test_progressive_rehash();
    printf("All hashtable tests passed.\n");
    return 0;
}
```

- [ ] **Step 2: Create the Makefile and confirm the test fails to build**

Create `Makefile`:

```makefile
CC := cc
CFLAGS := -std=c11 -Wall -Wextra
RELEASE_FLAGS := -O2
ASAN_FLAGS := -fsanitize=address -g

SRC_DIR := src
TEST_DIR := test
BUILD_DIR := build

.PHONY: all test clean test-hashtable

all: $(BUILD_DIR)/server $(BUILD_DIR)/client

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

test: test-hashtable

test-hashtable: $(BUILD_DIR)/test_hashtable
	$(BUILD_DIR)/test_hashtable

$(BUILD_DIR)/test_hashtable: $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/hashtable.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c

clean:
	rm -rf $(BUILD_DIR)
```

Create `.gitignore`:

```
build/
```

Run: `make test-hashtable`
Expected: FAIL — `cc` errors because `src/hashtable.h` and `src/hashtable.c` don't exist yet (`fatal error: 'hashtable.h' file not found` or similar).

- [ ] **Step 3: Write the implementation**

Create `src/hashtable.h`:

```c
#ifndef HASHTABLE_H
#define HASHTABLE_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct HNode {
    struct HNode *next;
    uint64_t hcode;
} HNode;

typedef struct {
    HNode **tab;
    size_t mask;
    size_t size;
} HTab;

typedef struct {
    HTab newer;
    HTab older;
    size_t migrate_pos;
} HMap;

typedef bool (*HEqFn)(HNode *node, HNode *key);

void hm_init(HMap *map);
void hm_insert(HMap *map, HNode *node);
HNode *hm_lookup(HMap *map, HNode *key, HEqFn eq);
HNode *hm_pop(HMap *map, HNode *key, HEqFn eq);
size_t hm_size(const HMap *map);
void hm_destroy(HMap *map, void (*free_node)(HNode *node));

uint64_t hash_bytes(const uint8_t *data, size_t len);

#endif
```

Create `src/hashtable.c`:

```c
#include <stdlib.h>
#include <assert.h>
#include "hashtable.h"

#define HT_INIT_SIZE 4
#define HT_MAX_LOAD_FACTOR 8
#define HT_REHASH_WORK 128

static void h_init(HTab *htab, size_t n) {
    assert(n > 0 && ((n - 1) & n) == 0); /* n must be a power of two */
    htab->tab = (HNode **)calloc(n, sizeof(HNode *));
    htab->mask = n - 1;
    htab->size = 0;
}

static void h_insert(HTab *htab, HNode *node) {
    size_t pos = node->hcode & htab->mask;
    node->next = htab->tab[pos];
    htab->tab[pos] = node;
    htab->size++;
}

static HNode **h_lookup(HTab *htab, HNode *key, HEqFn eq) {
    if (!htab->tab) {
        return NULL;
    }
    size_t pos = key->hcode & htab->mask;
    HNode **from = &htab->tab[pos];
    for (HNode *cur; (cur = *from) != NULL; from = &cur->next) {
        if (cur->hcode == key->hcode && eq(cur, key)) {
            return from;
        }
    }
    return NULL;
}

static HNode *h_detach(HTab *htab, HNode **from) {
    HNode *node = *from;
    *from = node->next;
    htab->size--;
    return node;
}

static void hm_start_resizing(HMap *map) {
    assert(map->older.tab == NULL);
    map->older = map->newer;
    h_init(&map->newer, (map->older.mask + 1) * 2);
    map->migrate_pos = 0;
}

static void hm_help_rehashing(HMap *map) {
    size_t nwork = 0;
    while (nwork < HT_REHASH_WORK && map->older.size > 0) {
        HNode **from = &map->older.tab[map->migrate_pos];
        if (!*from) {
            map->migrate_pos++;
            continue;
        }
        h_insert(&map->newer, h_detach(&map->older, from));
        nwork++;
    }
    if (map->older.size == 0 && map->older.tab) {
        free(map->older.tab);
        map->older = (HTab){0};
    }
}

void hm_init(HMap *map) {
    *map = (HMap){0};
}

void hm_insert(HMap *map, HNode *node) {
    if (!map->newer.tab) {
        h_init(&map->newer, HT_INIT_SIZE);
    }
    h_insert(&map->newer, node);

    if (!map->older.tab) {
        size_t threshold = (map->newer.mask + 1) * HT_MAX_LOAD_FACTOR;
        if (map->newer.size >= threshold) {
            hm_start_resizing(map);
        }
    }
    hm_help_rehashing(map);
}

HNode *hm_lookup(HMap *map, HNode *key, HEqFn eq) {
    HNode **from = h_lookup(&map->newer, key, eq);
    if (!from) {
        from = h_lookup(&map->older, key, eq);
    }
    return from ? *from : NULL;
}

HNode *hm_pop(HMap *map, HNode *key, HEqFn eq) {
    HNode **from = h_lookup(&map->newer, key, eq);
    if (from) {
        HNode *node = h_detach(&map->newer, from);
        hm_help_rehashing(map);
        return node;
    }
    from = h_lookup(&map->older, key, eq);
    if (from) {
        HNode *node = h_detach(&map->older, from);
        hm_help_rehashing(map);
        return node;
    }
    return NULL;
}

size_t hm_size(const HMap *map) {
    return map->newer.size + map->older.size;
}

void hm_destroy(HMap *map, void (*free_node)(HNode *node)) {
    for (size_t i = 0; map->newer.tab && i <= map->newer.mask; i++) {
        for (HNode *node = map->newer.tab[i]; node;) {
            HNode *next = node->next;
            if (free_node) {
                free_node(node);
            }
            node = next;
        }
    }
    for (size_t i = 0; map->older.tab && i <= map->older.mask; i++) {
        for (HNode *node = map->older.tab[i]; node;) {
            HNode *next = node->next;
            if (free_node) {
                free_node(node);
            }
            node = next;
        }
    }
    free(map->newer.tab);
    free(map->older.tab);
    *map = (HMap){0};
}

uint64_t hash_bytes(const uint8_t *data, size_t len) {
    uint64_t h = 0xcbf29ce484222325ULL; /* FNV offset basis */
    for (size_t i = 0; i < len; i++) {
        h ^= data[i];
        h *= 0x100000001b3ULL; /* FNV prime */
    }
    return h;
}
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `make test-hashtable`
Expected:
```
test_insert_and_lookup: OK
test_delete: OK
test_collision_chaining: OK
test_progressive_rehash: OK
All hashtable tests passed.
```

- [ ] **Step 5: Commit**

```bash
git add Makefile .gitignore src/hashtable.h src/hashtable.c test/test_hashtable.c
git commit -m "Add intrusive chaining hashtable with progressive rehashing"
```

---

## Task 2: Protocol module

**Files:**
- Modify: `Makefile`
- Create: `src/protocol.h`
- Create: `src/protocol.c`
- Test: `test/test_protocol.c`

**Interfaces:**
- Consumes: nothing from Task 1 (independent module).
- Produces (used by Task 3's `server.c` and `client.c`):
  - `#define K_MAX_MSG 4096`
  - `#define SERVER_PORT 1234`
  - `typedef enum { RES_OK = 0, RES_ERR = 1, RES_NX = 2 } ResponseStatus;`
  - `typedef struct { uint8_t *data; size_t len; size_t cap; } Buffer;`
  - `void buf_init(Buffer *buf);`
  - `void buf_free(Buffer *buf);`
  - `void buf_append(Buffer *buf, const uint8_t *data, size_t len);`
  - `void buf_consume(Buffer *buf, size_t n);`
  - `int encode_request(Buffer *out, char **args, const size_t *arglens, size_t nargs);` — returns 0, or -1 if the encoded message would exceed `K_MAX_MSG`.
  - `int parse_request(const uint8_t *data, size_t len, char ***out_args, size_t **out_arglens, size_t *out_nargs);` — returns 0 on success (caller must `free_request_args`), -1 if malformed.
  - `void free_request_args(char **args, size_t *arglens, size_t nargs);`
  - `void encode_response(Buffer *out, ResponseStatus status, const uint8_t *data, size_t datalen);`
  - `int parse_response(const uint8_t *data, size_t len, ResponseStatus *out_status, const uint8_t **out_data, size_t *out_datalen);` — `*out_data` points into `data` (no copy).
  - `int try_parse_frame(const uint8_t *buf, size_t buf_len, size_t *out_frame_len, size_t *out_payload_len);` — returns 1 if a complete frame is present (payload starts at `buf + 4`), 0 if more data is needed, -1 if the declared length exceeds `K_MAX_MSG`.
  - `int read_full(int fd, uint8_t *buf, size_t n);`
  - `int write_all(int fd, const uint8_t *buf, size_t n);`
  - `int read_frame(int fd, Buffer *out);` — appends the full frame (4-byte header + payload) to `out`.
  - `int write_frame(int fd, const uint8_t *payload, size_t len);`

- [ ] **Step 1: Write the failing test**

Create `test/test_protocol.c`:

```c
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include "../src/protocol.h"

static void test_buffer_append_grows(void) {
    Buffer buf;
    buf_init(&buf);
    for (int i = 0; i < 1000; i++) {
        uint8_t b = (uint8_t)i;
        buf_append(&buf, &b, 1);
    }
    assert(buf.len == 1000);
    for (int i = 0; i < 1000; i++) {
        assert(buf.data[i] == (uint8_t)i);
    }
    buf_free(&buf);
    printf("test_buffer_append_grows: OK\n");
}

static void test_buffer_consume(void) {
    Buffer buf;
    buf_init(&buf);
    buf_append(&buf, (const uint8_t *)"hello world", 11);
    buf_consume(&buf, 6);
    assert(buf.len == 5);
    assert(memcmp(buf.data, "world", 5) == 0);
    buf_free(&buf);
    printf("test_buffer_consume: OK\n");
}

static void test_request_roundtrip(void) {
    char *args[] = {"set", "foo", "bar"};
    size_t arglens[] = {3, 3, 3};

    Buffer out;
    buf_init(&out);
    assert(encode_request(&out, args, arglens, 3) == 0);

    char **parsed_args;
    size_t *parsed_lens;
    size_t nargs;
    assert(parse_request(out.data, out.len, &parsed_args, &parsed_lens, &nargs) == 0);
    assert(nargs == 3);
    assert(strcmp(parsed_args[0], "set") == 0);
    assert(strcmp(parsed_args[1], "foo") == 0);
    assert(strcmp(parsed_args[2], "bar") == 0);
    assert(parsed_lens[1] == 3);

    free_request_args(parsed_args, parsed_lens, nargs);
    buf_free(&out);
    printf("test_request_roundtrip: OK\n");
}

static void test_request_rejects_truncated(void) {
    uint8_t bad[4];
    uint32_t n = 5; /* claims 5 args but no data follows */
    memcpy(bad, &n, 4);
    char **args;
    size_t *lens;
    size_t nargs;
    assert(parse_request(bad, 4, &args, &lens, &nargs) == -1);
    printf("test_request_rejects_truncated: OK\n");
}

static void test_response_roundtrip_with_data(void) {
    Buffer out;
    buf_init(&out);
    encode_response(&out, RES_OK, (const uint8_t *)"bar", 3);

    ResponseStatus status;
    const uint8_t *data;
    size_t datalen;
    assert(parse_response(out.data, out.len, &status, &data, &datalen) == 0);
    assert(status == RES_OK);
    assert(datalen == 3);
    assert(memcmp(data, "bar", 3) == 0);

    buf_free(&out);
    printf("test_response_roundtrip_with_data: OK\n");
}

static void test_response_roundtrip_status_only(void) {
    Buffer out;
    buf_init(&out);
    encode_response(&out, RES_NX, NULL, 0);

    ResponseStatus status;
    const uint8_t *data;
    size_t datalen;
    assert(parse_response(out.data, out.len, &status, &data, &datalen) == 0);
    assert(status == RES_NX);
    assert(datalen == 0);

    buf_free(&out);
    printf("test_response_roundtrip_status_only: OK\n");
}

static void test_try_parse_frame(void) {
    Buffer payload;
    buf_init(&payload);
    encode_response(&payload, RES_OK, (const uint8_t *)"hi", 2);

    Buffer framed;
    buf_init(&framed);
    uint32_t l = (uint32_t)payload.len;
    buf_append(&framed, (uint8_t *)&l, 4);
    buf_append(&framed, payload.data, payload.len);

    size_t frame_len, payload_len;
    assert(try_parse_frame(framed.data, 4, &frame_len, &payload_len) == 0);
    assert(try_parse_frame(framed.data, 4 + payload.len - 1, &frame_len, &payload_len) == 0);

    int rv = try_parse_frame(framed.data, framed.len, &frame_len, &payload_len);
    assert(rv == 1);
    assert(frame_len == framed.len);
    assert(payload_len == payload.len);

    buf_free(&payload);
    buf_free(&framed);
    printf("test_try_parse_frame: OK\n");
}

static void test_try_parse_frame_rejects_oversized(void) {
    uint8_t buf[4];
    uint32_t huge = K_MAX_MSG + 1;
    memcpy(buf, &huge, 4);
    size_t frame_len, payload_len;
    assert(try_parse_frame(buf, 4, &frame_len, &payload_len) == -1);
    printf("test_try_parse_frame_rejects_oversized: OK\n");
}

static void test_frame_io_over_socketpair(void) {
    int fds[2];
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, fds) == 0);

    assert(write_frame(fds[0], (const uint8_t *)"ping", 4) == 0);

    Buffer got;
    buf_init(&got);
    assert(read_frame(fds[1], &got) == 0);
    assert(got.len == 4 + 4);
    assert(memcmp(got.data + 4, "ping", 4) == 0);

    buf_free(&got);
    close(fds[0]);
    close(fds[1]);
    printf("test_frame_io_over_socketpair: OK\n");
}

int main(void) {
    test_buffer_append_grows();
    test_buffer_consume();
    test_request_roundtrip();
    test_request_rejects_truncated();
    test_response_roundtrip_with_data();
    test_response_roundtrip_status_only();
    test_try_parse_frame();
    test_try_parse_frame_rejects_oversized();
    test_frame_io_over_socketpair();
    printf("All protocol tests passed.\n");
    return 0;
}
```

- [ ] **Step 2: Update the Makefile and confirm the test fails to build**

Overwrite `Makefile` with:

```makefile
CC := cc
CFLAGS := -std=c11 -Wall -Wextra
RELEASE_FLAGS := -O2
ASAN_FLAGS := -fsanitize=address -g

SRC_DIR := src
TEST_DIR := test
BUILD_DIR := build

.PHONY: all test clean test-hashtable test-protocol

all: $(BUILD_DIR)/server $(BUILD_DIR)/client

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

test: test-hashtable test-protocol

test-hashtable: $(BUILD_DIR)/test_hashtable
	$(BUILD_DIR)/test_hashtable

test-protocol: $(BUILD_DIR)/test_protocol
	$(BUILD_DIR)/test_protocol

$(BUILD_DIR)/test_hashtable: $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/hashtable.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c

$(BUILD_DIR)/test_protocol: $(TEST_DIR)/test_protocol.c $(SRC_DIR)/protocol.c $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_protocol.c $(SRC_DIR)/protocol.c

clean:
	rm -rf $(BUILD_DIR)
```

Run: `make test-protocol`
Expected: FAIL — `cc` errors because `src/protocol.h` and `src/protocol.c` don't exist yet.

- [ ] **Step 3: Write the implementation**

Create `src/protocol.h`:

```c
#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#define K_MAX_MSG 4096
#define SERVER_PORT 1234

typedef enum {
    RES_OK = 0,
    RES_ERR = 1,
    RES_NX = 2,
} ResponseStatus;

typedef struct {
    uint8_t *data;
    size_t len;
    size_t cap;
} Buffer;

void buf_init(Buffer *buf);
void buf_free(Buffer *buf);
void buf_append(Buffer *buf, const uint8_t *data, size_t len);
void buf_consume(Buffer *buf, size_t n);

int encode_request(Buffer *out, char **args, const size_t *arglens, size_t nargs);
int parse_request(const uint8_t *data, size_t len, char ***out_args, size_t **out_arglens, size_t *out_nargs);
void free_request_args(char **args, size_t *arglens, size_t nargs);

void encode_response(Buffer *out, ResponseStatus status, const uint8_t *data, size_t datalen);
int parse_response(const uint8_t *data, size_t len, ResponseStatus *out_status, const uint8_t **out_data, size_t *out_datalen);

int try_parse_frame(const uint8_t *buf, size_t buf_len, size_t *out_frame_len, size_t *out_payload_len);

int read_full(int fd, uint8_t *buf, size_t n);
int write_all(int fd, const uint8_t *buf, size_t n);
int read_frame(int fd, Buffer *out);
int write_frame(int fd, const uint8_t *payload, size_t len);

#endif
```

Create `src/protocol.c`:

```c
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>
#include "protocol.h"

void buf_init(Buffer *buf) {
    buf->data = NULL;
    buf->len = 0;
    buf->cap = 0;
}

void buf_free(Buffer *buf) {
    free(buf->data);
    buf_init(buf);
}

void buf_append(Buffer *buf, const uint8_t *data, size_t len) {
    if (buf->len + len > buf->cap) {
        size_t new_cap = buf->cap ? buf->cap * 2 : 64;
        while (new_cap < buf->len + len) {
            new_cap *= 2;
        }
        buf->data = realloc(buf->data, new_cap);
        buf->cap = new_cap;
    }
    memcpy(buf->data + buf->len, data, len);
    buf->len += len;
}

void buf_consume(Buffer *buf, size_t n) {
    assert(n <= buf->len);
    memmove(buf->data, buf->data + n, buf->len - n);
    buf->len -= n;
}

int encode_request(Buffer *out, char **args, const size_t *arglens, size_t nargs) {
    uint32_t n = (uint32_t)nargs;
    buf_append(out, (uint8_t *)&n, 4);
    for (size_t i = 0; i < nargs; i++) {
        uint32_t l = (uint32_t)arglens[i];
        buf_append(out, (uint8_t *)&l, 4);
        buf_append(out, (uint8_t *)args[i], arglens[i]);
    }
    if (out->len > K_MAX_MSG) {
        return -1;
    }
    return 0;
}

int parse_request(const uint8_t *data, size_t len, char ***out_args, size_t **out_arglens, size_t *out_nargs) {
    if (len < 4) {
        return -1;
    }
    uint32_t nargs;
    memcpy(&nargs, data, 4);
    if (nargs > 1024) {
        return -1;
    }
    size_t pos = 4;

    char **args = malloc(sizeof(char *) * (nargs ? nargs : 1));
    size_t *arglens = malloc(sizeof(size_t) * (nargs ? nargs : 1));

    for (uint32_t i = 0; i < nargs; i++) {
        if (pos + 4 > len) {
            for (uint32_t j = 0; j < i; j++) {
                free(args[j]);
            }
            free(args);
            free(arglens);
            return -1;
        }
        uint32_t l;
        memcpy(&l, data + pos, 4);
        pos += 4;
        if (pos + l > len) {
            for (uint32_t j = 0; j < i; j++) {
                free(args[j]);
            }
            free(args);
            free(arglens);
            return -1;
        }
        char *s = malloc(l + 1);
        memcpy(s, data + pos, l);
        s[l] = '\0';
        args[i] = s;
        arglens[i] = l;
        pos += l;
    }
    if (pos != len) {
        for (uint32_t j = 0; j < nargs; j++) {
            free(args[j]);
        }
        free(args);
        free(arglens);
        return -1;
    }

    *out_args = args;
    *out_arglens = arglens;
    *out_nargs = nargs;
    return 0;
}

void free_request_args(char **args, size_t *arglens, size_t nargs) {
    for (size_t i = 0; i < nargs; i++) {
        free(args[i]);
    }
    free(args);
    free(arglens);
}

void encode_response(Buffer *out, ResponseStatus status, const uint8_t *data, size_t datalen) {
    uint8_t s = (uint8_t)status;
    buf_append(out, &s, 1);
    if (data && datalen > 0) {
        uint32_t l = (uint32_t)datalen;
        buf_append(out, (uint8_t *)&l, 4);
        buf_append(out, data, datalen);
    }
}

int parse_response(const uint8_t *data, size_t len, ResponseStatus *out_status, const uint8_t **out_data, size_t *out_datalen) {
    if (len < 1) {
        return -1;
    }
    *out_status = (ResponseStatus)data[0];
    if (len == 1) {
        *out_data = NULL;
        *out_datalen = 0;
        return 0;
    }
    if (len < 5) {
        return -1;
    }
    uint32_t l;
    memcpy(&l, data + 1, 4);
    if (5 + (size_t)l != len) {
        return -1;
    }
    *out_data = data + 5;
    *out_datalen = l;
    return 0;
}

int try_parse_frame(const uint8_t *buf, size_t buf_len, size_t *out_frame_len, size_t *out_payload_len) {
    if (buf_len < 4) {
        return 0;
    }
    uint32_t len;
    memcpy(&len, buf, 4);
    if (len > K_MAX_MSG) {
        return -1;
    }
    if (buf_len < 4 + (size_t)len) {
        return 0;
    }
    *out_frame_len = 4 + len;
    *out_payload_len = len;
    return 1;
}

int read_full(int fd, uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = read(fd, buf, n);
        if (rv <= 0) {
            return -1;
        }
        n -= (size_t)rv;
        buf += rv;
    }
    return 0;
}

int write_all(int fd, const uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = write(fd, buf, n);
        if (rv <= 0) {
            return -1;
        }
        n -= (size_t)rv;
        buf += rv;
    }
    return 0;
}

int read_frame(int fd, Buffer *out) {
    uint8_t head[4];
    if (read_full(fd, head, 4) != 0) {
        return -1;
    }
    uint32_t len;
    memcpy(&len, head, 4);
    if (len > K_MAX_MSG) {
        return -1;
    }
    buf_append(out, head, 4);
    if (len > 0) {
        uint8_t tmp[K_MAX_MSG];
        if (read_full(fd, tmp, len) != 0) {
            return -1;
        }
        buf_append(out, tmp, len);
    }
    return 0;
}

int write_frame(int fd, const uint8_t *payload, size_t len) {
    if (len > K_MAX_MSG) {
        return -1;
    }
    uint8_t head[4];
    uint32_t l = (uint32_t)len;
    memcpy(head, &l, 4);
    if (write_all(fd, head, 4) != 0) {
        return -1;
    }
    if (len > 0 && write_all(fd, payload, len) != 0) {
        return -1;
    }
    return 0;
}
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `make test-protocol`
Expected:
```
test_buffer_append_grows: OK
test_buffer_consume: OK
test_request_roundtrip: OK
test_request_rejects_truncated: OK
test_response_roundtrip_with_data: OK
test_response_roundtrip_status_only: OK
test_try_parse_frame: OK
test_try_parse_frame_rejects_oversized: OK
test_frame_io_over_socketpair: OK
All protocol tests passed.
```

- [ ] **Step 5: Commit**

```bash
git add Makefile src/protocol.h src/protocol.c test/test_protocol.c
git commit -m "Add length-prefixed wire protocol with encode/parse/framing"
```

---

## Task 3: Server and client binaries

**Files:**
- Modify: `Makefile`
- Create: `src/server.c`
- Create: `src/client.c`

**Interfaces:**
- Consumes: everything from Task 1 (`hashtable.h`) and Task 2 (`protocol.h`), exact signatures as listed above.
- Produces: `build/server` (listens on `127.0.0.1:1234`), `build/client` (argv-driven: `./build/client <cmd> [args...]`, prints the value / `OK` / `(nil)` / `(error) ...` to stdout).

- [ ] **Step 1: Write `src/server.c`**

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include "hashtable.h"
#include "protocol.h"

typedef struct Entry {
    HNode node;
    char *key;
    size_t keylen;
    char *val;
    size_t vallen;
} Entry;

static HMap g_data;

static bool entry_eq(HNode *lhs, HNode *rhs) {
    Entry *le = (Entry *)lhs;
    Entry *re = (Entry *)rhs;
    return le->keylen == re->keylen && memcmp(le->key, re->key, le->keylen) == 0;
}

static void entry_free(HNode *node) {
    Entry *e = (Entry *)node;
    free(e->key);
    free(e->val);
    free(e);
}

typedef struct Conn {
    int fd;
    bool want_read;
    bool want_write;
    bool want_close;
    Buffer incoming;
    Buffer outgoing;
} Conn;

static Conn **g_fd2conn = NULL;
static size_t g_fd2conn_cap = 0;

static void die(const char *msg) {
    perror(msg);
    exit(1);
}

static void set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) {
        die("fcntl(F_GETFL)");
    }
    if (fcntl(fd, F_SETFL, flags | O_NONBLOCK) == -1) {
        die("fcntl(F_SETFL)");
    }
}

static void fd2conn_put(int fd, Conn *conn) {
    if ((size_t)fd >= g_fd2conn_cap) {
        size_t new_cap = g_fd2conn_cap ? g_fd2conn_cap * 2 : 16;
        while (new_cap <= (size_t)fd) {
            new_cap *= 2;
        }
        g_fd2conn = realloc(g_fd2conn, new_cap * sizeof(Conn *));
        for (size_t i = g_fd2conn_cap; i < new_cap; i++) {
            g_fd2conn[i] = NULL;
        }
        g_fd2conn_cap = new_cap;
    }
    g_fd2conn[fd] = conn;
}

static void do_get(char **args, size_t *arglens, Buffer *out) {
    Entry key = {0};
    key.key = args[1];
    key.keylen = arglens[1];
    key.node.hcode = hash_bytes((const uint8_t *)key.key, key.keylen);

    HNode *node = hm_lookup(&g_data, &key.node, entry_eq);
    if (!node) {
        encode_response(out, RES_NX, NULL, 0);
        return;
    }
    Entry *e = (Entry *)node;
    encode_response(out, RES_OK, (uint8_t *)e->val, e->vallen);
}

static void do_set(char **args, size_t *arglens, Buffer *out) {
    Entry key = {0};
    key.key = args[1];
    key.keylen = arglens[1];
    key.node.hcode = hash_bytes((const uint8_t *)key.key, key.keylen);

    HNode *node = hm_lookup(&g_data, &key.node, entry_eq);
    if (node) {
        Entry *e = (Entry *)node;
        free(e->val);
        e->val = malloc(arglens[2]);
        memcpy(e->val, args[2], arglens[2]);
        e->vallen = arglens[2];
    } else {
        Entry *e = malloc(sizeof(Entry));
        e->key = malloc(arglens[1]);
        memcpy(e->key, args[1], arglens[1]);
        e->keylen = arglens[1];
        e->val = malloc(arglens[2]);
        memcpy(e->val, args[2], arglens[2]);
        e->vallen = arglens[2];
        e->node.next = NULL;
        e->node.hcode = key.node.hcode;
        hm_insert(&g_data, &e->node);
    }
    encode_response(out, RES_OK, NULL, 0);
}

static void do_del(char **args, size_t *arglens, Buffer *out) {
    Entry key = {0};
    key.key = args[1];
    key.keylen = arglens[1];
    key.node.hcode = hash_bytes((const uint8_t *)key.key, key.keylen);

    HNode *node = hm_pop(&g_data, &key.node, entry_eq);
    if (!node) {
        encode_response(out, RES_NX, NULL, 0);
        return;
    }
    entry_free(node);
    encode_response(out, RES_OK, NULL, 0);
}

static void do_request(char **args, size_t *arglens, size_t nargs, Buffer *out) {
    if (nargs == 2 && strcmp(args[0], "get") == 0) {
        do_get(args, arglens, out);
    } else if (nargs == 3 && strcmp(args[0], "set") == 0) {
        do_set(args, arglens, out);
    } else if (nargs == 2 && strcmp(args[0], "del") == 0) {
        do_del(args, arglens, out);
    } else {
        encode_response(out, RES_ERR, NULL, 0);
    }
}

static Conn *conn_new(int fd) {
    Conn *conn = malloc(sizeof(Conn));
    conn->fd = fd;
    conn->want_read = true;
    conn->want_write = false;
    conn->want_close = false;
    buf_init(&conn->incoming);
    buf_init(&conn->outgoing);
    return conn;
}

static void conn_destroy(Conn *conn) {
    close(conn->fd);
    buf_free(&conn->incoming);
    buf_free(&conn->outgoing);
    g_fd2conn[conn->fd] = NULL;
    free(conn);
}

static void process_buffered_requests(Conn *conn) {
    while (true) {
        size_t frame_len, payload_len;
        int rv = try_parse_frame(conn->incoming.data, conn->incoming.len, &frame_len, &payload_len);
        if (rv == 0) {
            break;
        }
        if (rv < 0) {
            conn->want_close = true;
            return;
        }
        const uint8_t *payload = conn->incoming.data + 4;
        char **args;
        size_t *arglens;
        size_t nargs;
        if (parse_request(payload, payload_len, &args, &arglens, &nargs) != 0) {
            conn->want_close = true;
            return;
        }
        do_request(args, arglens, nargs, &conn->outgoing);
        free_request_args(args, arglens, nargs);
        buf_consume(&conn->incoming, frame_len);
    }
}

static void handle_read(Conn *conn) {
    uint8_t tmp[64 * 1024];
    ssize_t rv = read(conn->fd, tmp, sizeof(tmp));
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv <= 0) {
        conn->want_close = true;
        return;
    }
    buf_append(&conn->incoming, tmp, (size_t)rv);
    process_buffered_requests(conn);
    conn->want_write = conn->outgoing.len > 0;
}

static void handle_write(Conn *conn) {
    ssize_t rv = write(conn->fd, conn->outgoing.data, conn->outgoing.len);
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv < 0) {
        conn->want_close = true;
        return;
    }
    buf_consume(&conn->outgoing, (size_t)rv);
    conn->want_write = conn->outgoing.len > 0;
}

static int make_listener(void) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        die("socket()");
    }

    int val = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &val, sizeof(val));

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        die("bind()");
    }
    if (listen(fd, SOMAXCONN) != 0) {
        die("listen()");
    }
    set_nonblocking(fd);
    return fd;
}

static void accept_new_conn(int listen_fd) {
    struct sockaddr_in client_addr = {0};
    socklen_t addrlen = sizeof(client_addr);
    int connfd = accept(listen_fd, (struct sockaddr *)&client_addr, &addrlen);
    if (connfd < 0) {
        return;
    }
    set_nonblocking(connfd);
    fd2conn_put(connfd, conn_new(connfd));
}

int main(void) {
    signal(SIGPIPE, SIG_IGN);
    hm_init(&g_data);

    int listen_fd = make_listener();
    fprintf(stderr, "listening on 127.0.0.1:%d\n", SERVER_PORT);

    struct pollfd *poll_args = NULL;
    size_t poll_cap = 0;

    while (true) {
        size_t nfds = 1;
        for (size_t i = 0; i < g_fd2conn_cap; i++) {
            if (g_fd2conn[i]) {
                nfds++;
            }
        }
        if (nfds > poll_cap) {
            poll_cap = nfds;
            poll_args = realloc(poll_args, poll_cap * sizeof(struct pollfd));
        }

        poll_args[0] = (struct pollfd){.fd = listen_fd, .events = POLLIN, .revents = 0};

        size_t n = 1;
        for (size_t i = 0; i < g_fd2conn_cap; i++) {
            Conn *conn = g_fd2conn[i];
            if (!conn) {
                continue;
            }
            struct pollfd pfd = {.fd = conn->fd, .events = POLLERR, .revents = 0};
            if (conn->want_read) {
                pfd.events |= POLLIN;
            }
            if (conn->want_write) {
                pfd.events |= POLLOUT;
            }
            poll_args[n++] = pfd;
        }

        int rv = poll(poll_args, (nfds_t)n, -1);
        if (rv < 0 && errno == EINTR) {
            continue;
        }
        if (rv < 0) {
            die("poll()");
        }

        if (poll_args[0].revents & POLLIN) {
            accept_new_conn(listen_fd);
        }

        for (size_t i = 1; i < n; i++) {
            short re = poll_args[i].revents;
            if (!re) {
                continue;
            }
            Conn *conn = g_fd2conn[poll_args[i].fd];
            if (!conn) {
                continue;
            }
            if (re & POLLIN) {
                handle_read(conn);
            }
            if (!conn->want_close && (re & POLLOUT)) {
                handle_write(conn);
            }
            if (conn->want_close || (re & (POLLERR | POLLHUP))) {
                conn_destroy(conn);
            }
        }
    }

    return 0;
}
```

- [ ] **Step 2: Write `src/client.c`**

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include "protocol.h"

static int connect_to_server(void) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket()");
        exit(1);
    }

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        perror("connect()");
        exit(1);
    }
    return fd;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s <cmd> [args...]\n", argv[0]);
        return 1;
    }

    size_t nargs = (size_t)(argc - 1);
    char **args = &argv[1];
    size_t *arglens = malloc(nargs * sizeof(size_t));
    for (size_t i = 0; i < nargs; i++) {
        arglens[i] = strlen(args[i]);
    }

    Buffer req;
    buf_init(&req);
    if (encode_request(&req, args, arglens, nargs) != 0) {
        fprintf(stderr, "request too large\n");
        return 1;
    }

    int fd = connect_to_server();
    if (write_frame(fd, req.data, req.len) != 0) {
        fprintf(stderr, "write_frame failed\n");
        return 1;
    }

    Buffer resp;
    buf_init(&resp);
    if (read_frame(fd, &resp) != 0) {
        fprintf(stderr, "read_frame failed\n");
        return 1;
    }

    ResponseStatus status;
    const uint8_t *data;
    size_t datalen;
    if (parse_response(resp.data + 4, resp.len - 4, &status, &data, &datalen) != 0) {
        fprintf(stderr, "bad response\n");
        return 1;
    }

    switch (status) {
    case RES_OK:
        if (datalen > 0) {
            fwrite(data, 1, datalen, stdout);
            fputc('\n', stdout);
        } else {
            printf("OK\n");
        }
        break;
    case RES_NX:
        printf("(nil)\n");
        break;
    case RES_ERR:
        printf("(error) unknown command or wrong number of arguments\n");
        break;
    }

    close(fd);
    buf_free(&req);
    buf_free(&resp);
    free(arglens);
    return 0;
}
```

- [ ] **Step 3: Update the Makefile to build both binaries**

Overwrite `Makefile` with:

```makefile
CC := cc
CFLAGS := -std=c11 -Wall -Wextra
RELEASE_FLAGS := -O2
ASAN_FLAGS := -fsanitize=address -g

SRC_DIR := src
TEST_DIR := test
BUILD_DIR := build

.PHONY: all test clean test-hashtable test-protocol

all: $(BUILD_DIR)/server $(BUILD_DIR)/client

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/server: $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c $(SRC_DIR)/hashtable.h $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c

$(BUILD_DIR)/client: $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c

test: test-hashtable test-protocol

test-hashtable: $(BUILD_DIR)/test_hashtable
	$(BUILD_DIR)/test_hashtable

test-protocol: $(BUILD_DIR)/test_protocol
	$(BUILD_DIR)/test_protocol

$(BUILD_DIR)/test_hashtable: $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/hashtable.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c

$(BUILD_DIR)/test_protocol: $(TEST_DIR)/test_protocol.c $(SRC_DIR)/protocol.c $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_protocol.c $(SRC_DIR)/protocol.c

clean:
	rm -rf $(BUILD_DIR)
```

Run: `make all`
Expected: both `build/server` and `build/client` compile with no warnings.

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

- [ ] **Step 5: Commit**

```bash
git add Makefile src/server.c src/client.c
git commit -m "Add poll-based key-value server and companion client"
```

---

## Task 4: ASan test binaries and automated integration test

**Files:**
- Modify: `Makefile`
- Create: `test/test_integration.sh`

**Interfaces:**
- Consumes: `build/server_asan` and `build/client_asan` (ASan-instrumented builds of `server.c`/`client.c` from Task 3, same behavior as the release binaries).
- Produces: `make test` — runs hashtable unit tests, protocol unit tests, and the integration script; exits non-zero on any failure.

- [ ] **Step 1: Write `test/test_integration.sh`**

Create `test/test_integration.sh` (make it executable):

```bash
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
```

Run: `chmod +x test/test_integration.sh`

- [ ] **Step 2: Update the Makefile to add ASan binaries and wire up `make test`**

Overwrite `Makefile` with:

```makefile
CC := cc
CFLAGS := -std=c11 -Wall -Wextra
RELEASE_FLAGS := -O2
ASAN_FLAGS := -fsanitize=address -g

SRC_DIR := src
TEST_DIR := test
BUILD_DIR := build

.PHONY: all test clean test-hashtable test-protocol test-integration

all: $(BUILD_DIR)/server $(BUILD_DIR)/client

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/server: $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c $(SRC_DIR)/hashtable.h $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c

$(BUILD_DIR)/client: $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c

$(BUILD_DIR)/server_asan: $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c $(SRC_DIR)/hashtable.h $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c

$(BUILD_DIR)/client_asan: $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c

test: test-hashtable test-protocol test-integration

test-hashtable: $(BUILD_DIR)/test_hashtable
	$(BUILD_DIR)/test_hashtable

test-protocol: $(BUILD_DIR)/test_protocol
	$(BUILD_DIR)/test_protocol

test-integration: $(BUILD_DIR)/server_asan $(BUILD_DIR)/client_asan
	$(TEST_DIR)/test_integration.sh

$(BUILD_DIR)/test_hashtable: $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/hashtable.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c

$(BUILD_DIR)/test_protocol: $(TEST_DIR)/test_protocol.c $(SRC_DIR)/protocol.c $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_protocol.c $(SRC_DIR)/protocol.c

clean:
	rm -rf $(BUILD_DIR)
```

- [ ] **Step 3: Run the full test suite and confirm it passes**

Run: `make clean && make test`
Expected: hashtable and protocol unit test output (as in Tasks 1-2), followed by:
```
Inserting 10000 keys to force a resize (this takes roughly a minute)...
Verifying a sample of keys survived rehashing...
All integration tests passed.
```
with a zero exit code and no AddressSanitizer error reports in the output.

- [ ] **Step 4: Commit**

```bash
git add Makefile test/test_integration.sh
git commit -m "Add ASan-instrumented binaries and end-to-end integration test"
```

---

## Final Verification

- [ ] Run `make clean && make all && make test` from the repo root — all four steps (build, hashtable tests, protocol tests, integration test) must succeed with no ASan errors.
- [ ] Manually run `./build/server &` and drive a few commands with `./build/client` to confirm the release binaries behave the same as the ASan ones.
