# 04 — `src/hashtable.h`

**What it is:** the interface of `HMap`, the hand-written hashtable that
stores every key-value pair. No networking in this file; it's pure data
structures, the closest thing to DSA in the project.

**Why not `std::unordered_map`?** The project follows the "Build Your Own
Redis" book, whose point is to learn how Redis's own hashtable works: two
tables and **incremental resizing**, so a resize never freezes the server.
`std::unordered_map` resizes everything at once. See
[05](05-hashtable.cpp.md) for the full explanation.

---

## Lines 1–6: guard and includes

```cpp
#ifndef HASHTABLE_H
#define HASHTABLE_H

#include <cstddef>   // size_t
#include <cstdint>   // uint64_t, uint8_t
#include <vector>    // std::vector
```

Include guard (see [02](02-protocol.h.md#lines-12-65-include-guard)) and the
types used below.

---

## Lines 8–12: `HNode`, the intrusive node

```cpp
// Intrusive node: embed it in your own struct (see Entry in server.cpp).
struct HNode {
    HNode *next = nullptr;
    uint64_t hcode = 0;
};
```

Each bucket of a chaining hashtable is a linked list. `HNode` is one link:
- `next`: the next node in the same bucket (or `nullptr`).
- `hcode`: the key's hash, computed once and stored, so we never rehash a key
  while resizing, and we can skip most key comparisons (compare hashes first).

### What "intrusive" means

In DSA you'd write a list node that *contains* the data:

```cpp
struct Node { Node *next; std::string key, val; };   // "non-intrusive"
```

Here it's the other way round: **the data contains the node**. The server
does this:

```cpp
struct Entry : HNode {     // Entry "is an" HNode, plus key and value
    std::string key;
    std::string val;
};
```

The hashtable only ever sees `HNode*` pointers. It links them, unlinks them,
compares hashes, and never knows about keys or values. When the server gets
an `HNode*` back, it converts it to `Entry*` with `static_cast`.

Picture of one `Entry` in memory:

```
 Entry object
 ┌─────────────────────────┐
 │ HNode part: next, hcode │  <- the HMap only touches this
 ├─────────────────────────┤
 │ key (std::string)       │
 │ val (std::string)       │
 └─────────────────────────┘
```

**Why do it this way?**
- **No extra allocation:** one `new Entry` covers both the node and the data.
- **Generic without templates:** the same `HMap` works for any struct that
  inherits `HNode` (the unit test uses `TestNode` with int keys).
- **One object in several structures:** in later chapters of the book, one
  entry is also linked into a sorted tree and a TTL heap at the same time,
  by embedding several node types. The Linux kernel uses this pattern
  everywhere (`list_head`).

> **C++ note — default member initializers:** `HNode *next = nullptr;` gives
> the field a default value whenever an `HNode` is created, so it's never
> garbage.

---

## Lines 14–15: function pointer types

```cpp
using EqFn = bool (*)(const HNode *a, const HNode *b);
using DeleteFn = void (*)(HNode *node);
```

Since `HMap` doesn't know what's inside a node, it needs the user to tell it
two things:
- **`EqFn`**: how to check whether two nodes have the same key.
- **`DeleteFn`**: how to free a node (the map calls it in its destructor for
  any entries still stored).

> **C++ note — reading `bool (*)(const HNode *, const HNode *)`:** "a
> pointer to a function that takes two `const HNode*` and returns `bool`".
> `using EqFn = ...;` gives that type a short name. Any plain function with
> that signature can be passed, e.g. `entryEq` in `server.cpp`. It's the
> same idea as passing a comparator to `std::sort` in DSA, except limited to
> plain functions (no capturing lambdas).

---

## Lines 17–22: class and constructor

```cpp
// Chained hashtable that resizes incrementally: when the load factor is hit,
// entries move from the old table to the new one a few at a time on each
// insert/pop, so no single operation pays for the whole resize.
class HMap {
public:
    HMap(EqFn eq, DeleteFn deleter) : eq_(eq), deleter_(deleter) {}
```

The constructor stores the two functions.

> **C++ note — member initializer list:** `: eq_(eq), deleter_(deleter)`
> initialises the members directly, before the constructor body `{}` runs.
> Preferred over assigning inside the body.

---

## Line 23: destructor

```cpp
    ~HMap();
```

Runs automatically when an `HMap` goes out of scope. It walks every
remaining node and passes it to `deleter_`, so nothing leaks. This is
**RAII** ("Resource Acquisition Is Initialization"): an object cleans up
what it owns when it dies, so you never need to remember a manual
`cleanup()` call.

---

## Lines 25–26: no copying

```cpp
    HMap(const HMap &) = delete;
    HMap &operator=(const HMap &) = delete;
```

Forbid copying an `HMap`. If you could copy it, the copy would hold the
**same** node pointers. When both copies were destroyed, each would delete
the same nodes: a **double free**, which crashes or corrupts memory. `= delete`
turns any attempt to copy into a compile error.

> **C++ note — rule of three:** if a class needs a custom destructor
> (because it owns something), it almost always needs custom copy behaviour
> too. Here "don't allow copying" is the simplest correct choice.

---

## Lines 28–31: the public API

```cpp
    void insert(HNode *node);
    HNode *lookup(const HNode *key) const;
    HNode *pop(const HNode *key);  // caller takes ownership of the result
    size_t size() const { return newer_.size + older_.size; }
```

| Method | What it does | Cost (average) |
|---|---|---|
| `insert(node)` | Add a node. Assumes the key isn't already present (the caller checks with `lookup` first). | O(1) |
| `lookup(key)` | Find the node with the same key, or `nullptr` | O(1) |
| `pop(key)` | Remove and return the matching node, or `nullptr`. **You** must delete it. | O(1) |
| `size()` | Number of stored nodes, counting both tables | O(1) |

**How do you look up by key if the map only takes `HNode*`?** You build a
temporary "probe" node with the key and hash filled in, and pass its
address. The map compares it against stored nodes using `eq_`. See
`KvStore::makeProbe` in `server.cpp`.

**Ownership rule:** the map owns nodes that are inside it. `pop` hands
ownership back to the caller. That's why `KvStore::del` calls `delete` on
what `pop` returns.

---

## Lines 33–38: `HTab`, one fixed-size table

```cpp
private:
    struct HTab {
        std::vector<HNode *> tab;
        size_t mask = 0;
        size_t size = 0;
    };
```

A single hashtable that never resizes itself:
- `tab`: the bucket array. `tab[i]` is the head of bucket `i`'s linked list.
- `mask`: bucket count minus 1. The number of buckets is always a power of
  two, so `hash & mask` gives the bucket index (see [05](05-hashtable.cpp.md)).
- `size`: number of nodes in this table.

`HMap` holds **two** of these, which is the key to incremental resizing.

> **C++ note — nested struct:** `HTab` is declared inside `HMap` and is
> private, so nothing outside the class can use it.

---

## Lines 40–46: private helpers

```cpp
    static void htabInit(HTab &htab, size_t n);
    static void htabInsert(HTab &htab, HNode *node);
    static HNode **htabLookup(HTab &htab, const HNode *key, EqFn eq);
    static HNode *htabDetach(HTab &htab, HNode **from);

    void startResizing();
    void helpRehashing();
```

The first four work on a single `HTab`. They're `static` because they don't
need an `HMap` object, only the table passed in.

`htabLookup` returns `HNode **` (a pointer to a pointer). This is the
cleverest trick in the codebase; it's explained in detail in
[05](05-hashtable.cpp.md#lines-2537-htablookup-the-pointer-to-pointer-trick).

`startResizing` and `helpRehashing` implement the incremental resize.

> **C++ note — `static` member function:** belongs to the class, not to an
> object. There's no `this`, so it can't touch `eq_`, `newer_`, etc. directly.
> That's why `eq` is passed in as a parameter.

---

## Lines 48–53: data members

```cpp
    EqFn eq_;
    DeleteFn deleter_;
    HTab newer_;
    HTab older_;  // non-empty only while a resize is in progress
    size_t migratePos_ = 0;
};
```

- `newer_`: the main table. New inserts always go here.
- `older_`: during a resize, holds the old, smaller table whose nodes are
  still being moved into `newer_`. Otherwise empty.
- `migratePos_`: which bucket of `older_` we're currently moving nodes from.

---

## Line 55: hash function

```cpp
uint64_t hashBytes(const uint8_t *data, size_t len);
```

Turns any sequence of bytes (a key) into a 64-bit hash (the FNV-1a
algorithm). A free function, not a member, so callers compute the hash
themselves and store it in `hcode` before inserting or looking up.
