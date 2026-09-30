# 09 — `test/test_hashtable.cpp`

**What it is:** unit tests for `HMap`, with no networking involved. It's
compiled with AddressSanitizer (`make test-hashtable`), so any memory bug in
the hashtable (use-after-free, leak, out-of-bounds) makes the test fail even
if the asserts pass.

**No test framework:** each test is a plain function that uses `assert`. If
an assert fails, the program aborts with the file and line number. If
`main` reaches the end, everything passed.

---

## Lines 1–4: includes

```cpp
#include <cassert>
#include <cstdio>

#include "../src/hashtable.h"
```

---

## Lines 6–17: a test node type

```cpp
struct TestNode : HNode {
    int key = 0;
    int val = 0;
};

static bool testEq(const HNode *a, const HNode *b) {
    return static_cast<const TestNode *>(a)->key == static_cast<const TestNode *>(b)->key;
}

static void deleteTestNode(HNode *node) {
    delete static_cast<TestNode *>(node);
}
```

The same pattern as `Entry` in the server, but with `int` keys. This proves
`HMap` really is generic: it works with any struct that inherits `HNode`.

---

## Lines 19–52: helpers

```cpp
static uint64_t hashInt(int key) {
    return hashBytes(reinterpret_cast<const uint8_t *>(&key), sizeof(key));
}
```

Hash an `int` by feeding its 4 raw bytes to FNV-1a.

```cpp
static TestNode *makeNode(int key, int val, uint64_t hcode) { ... }
```

Allocate a node with the given key, value and hash. The hash is a
parameter so one test can force collisions.

```cpp
static TestNode *find(const HMap &map, int key, uint64_t hcode) {
    TestNode probe;
    probe.key = key;
    probe.hcode = hcode;
    return static_cast<TestNode *>(map.lookup(&probe));
}

static TestNode *find(const HMap &map, int key) {
    return find(map, key, hashInt(key));
}
```

Look up by key, using a stack-allocated probe (same trick as
`KvStore::makeProbe`). The second overload computes the normal hash for you.

> **C++ note — `static_cast` of a null pointer:** if `lookup` returns
> `nullptr`, casting it gives a `nullptr` `TestNode*`. Safe.

> **C++ note — `const HMap &map`:** `find` only calls `lookup`, which is a
> `const` method, so it can take the map by const reference.

```cpp
static bool popAndDelete(HMap &map, int key) {
    ...
    HNode *popped = map.pop(&probe);
    if (!popped) {
        return false;
    }
    deleteTestNode(popped);
    return true;
}
```

Remove a key. Since `pop` gives ownership back to the caller, the test must
free the node; ASan would report a leak otherwise.

---

## Lines 54–62: `testInsertAndLookup`

Insert key 42 → value 100. Check that 42 is found with the right value and
that a missing key (99) returns `nullptr`.

When the function ends, `map` goes out of scope, and its destructor frees
the node through `deleteTestNode`. ASan would flag a leak if it didn't.

---

## Lines 64–74: `testDelete`

Insert key 7, pop it (returns true), pop it again (returns false, nothing
left), and check the size is 0 and a lookup fails.

---

## Lines 76–89: `testCollisionChaining`

```cpp
    for (int i = 0; i < 4; i++) {
        map.insert(makeNode(i, i * 10, 1));  // same hcode: all land in one bucket
    }
```

Give four different keys the **same** hash (`1`). They all land in the same
bucket, forming one chain of 4 nodes. Then check each is still found with
its own value.

This tests the case where hashes match but keys differ, i.e. that
`htabLookup` calls `eq` and doesn't stop at the first matching `hcode`.

---

## Lines 91–115: `testProgressiveRehash`

The most important test.

```cpp
    constexpr int kKeys = 5000;
    for (int i = 0; i < kKeys; i++) {
        map.insert(makeNode(i, i, hashInt(i)));
    }
```

5,000 inserts trigger 8 resizes (at 32, 64, 128, 256, 512, 1024, 2048 and
4096 entries), ending with 1,024 buckets. The larger resizes (from 256
entries up) can't finish in one call (128 moves per call), so nodes are
inserted into `newer_` while `older_` still holds entries. That's exactly the
two-table state that incremental resizing has to get right.

```cpp
    for (int i = 0; i < kKeys; i++) {
        assert(find(map, i) != nullptr);
        assert(find(map, i)->val == i);
    }
    assert(find(map, -1) == nullptr);
    assert(find(map, kKeys) == nullptr);
```

Every key must still be found with its original value; nothing was lost or
duplicated during migration. Keys that were never inserted must not be found.

```cpp
    for (int i = 0; i < kKeys; i += 2) {
        assert(popAndDelete(map, i));
    }
    assert(map.size() == kKeys / 2);
    for (int i = 0; i < kKeys; i++) {
        assert((find(map, i) == nullptr) == (i % 2 == 0));
    }
```

Delete every even key, then check: even keys are gone, odd keys remain.

The last assert reads as "*is missing* exactly when *is even*": both sides
are `bool`, and `==` checks they agree.

**What it doesn't cover:** by the time deletes start, the last resize has
finished (it only needed 32 inserts), so there's no test of `pop` or
`lookup` while a migration is in progress. A test that inserts, say, 4,100
keys and then immediately looks up and deletes would cover it.

---

## Lines 117–124: `main`

Run each test in order and print a success line. `assert` aborts on the
first failure, so reaching the final `printf` means all passed.
