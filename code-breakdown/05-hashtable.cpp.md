# 05 — `src/hashtable.cpp`

**What it is:** the implementation of `HMap`: a chaining hashtable with
power-of-two bucket counts and **incremental (progressive) resizing**.

Read [04 — hashtable.h](04-hashtable.h.md) first for the intrusive-node idea.

---

## The big idea before the code

### Chaining (you know this from DSA)

```
buckets:  [0] -> A -> D -> null
          [1] -> null
          [2] -> B -> null
          [3] -> C -> E -> F -> null
```

Hash the key, pick a bucket, walk that bucket's linked list.

### The problem: resizing freezes the server

When a hashtable gets too full, lists get long and lookups slow down, so you
allocate a bigger table and move every entry across. `std::unordered_map`
does that in one go. With 10 million keys, that single `insert` might take
hundreds of milliseconds, and our server is **single-threaded**: every
client waits during that time.

### The fix: resize a little at a time

Keep **two** tables during a resize:

```
 older_ (small, being emptied)       newer_ (2x bigger, being filled)
 [0] -> A -> D                       [0] ->
 [1] ->            ─ move 128 ─►     [1] -> X        <- new inserts go here
 [2] -> B            per call        ...
 [3] -> C -> E -> F                  [7] ->
       ^ migratePos_
```

- New inserts always go into `newer_`.
- Every `insert` and `pop` also moves up to **128** nodes from `older_` to
  `newer_` (`helpRehashing`).
- Lookups check `newer_` then `older_`, so every key is still findable
  mid-resize.
- When `older_` is empty, it's freed and we're back to one table.

The resize cost is spread over many operations, so no single request is
slow. Real Redis does the same thing (its `dict` has `ht[0]` and `ht[1]`).

---

## Lines 1–9: includes and tuning constants

```cpp
#include "hashtable.h"

#include <cassert>

namespace {
constexpr size_t kInitSize = 4;
constexpr size_t kMaxLoadFactor = 8;
constexpr size_t kRehashWork = 128;  // entries migrated per insert/pop
}  // namespace
```

| Constant | Meaning |
|---|---|
| `kInitSize = 4` | The first table has 4 buckets |
| `kMaxLoadFactor = 8` | Resize when there are 8 nodes per bucket on average |
| `kRehashWork = 128` | Move at most 128 nodes per `insert`/`pop` |

**Load factor** = nodes ÷ buckets. A load factor of 8 is high (Java's
`HashMap` uses 0.75, `std::unordered_map` uses 1.0), so chains average ~8
long. It trades a bit of lookup speed for less memory. It's the book's choice.

The anonymous `namespace {}` makes these constants private to this file.

---

## Lines 11–16: `htabInit`

```cpp
void HMap::htabInit(HTab &htab, size_t n) {
    assert(n > 0 && ((n - 1) & n) == 0);  // n must be a power of two
    htab.tab.assign(n, nullptr);
    htab.mask = n - 1;
    htab.size = 0;
}
```

Set up an empty table with `n` buckets.

**The power-of-two check:** a power of two has exactly one `1` bit.
Subtracting 1 turns that bit off and every lower bit on, so AND-ing them
gives 0:

```
n     = 8 = 1000
n - 1 = 7 = 0111
n & (n-1) = 0000  -> power of two ✓

n     = 6 = 0110
n - 1 = 5 = 0101
n & (n-1) = 0100  -> not a power of two ✗
```

(You may know this trick from DSA bit-manipulation problems.)

`tab.assign(n, nullptr)` resizes the bucket vector to `n` entries, all
empty. `mask = n - 1` is used for fast bucket selection below.

---

## Lines 18–23: `htabInsert`

```cpp
void HMap::htabInsert(HTab &htab, HNode *node) {
    size_t pos = node->hcode & htab.mask;
    node->next = htab.tab[pos];
    htab.tab[pos] = node;
    htab.size++;
}
```

1. **Pick the bucket:** `hcode & mask`. With `n` a power of two, this equals
   `hcode % n` but is a single fast AND instruction instead of a slow
   division.

   ```
   n = 8, mask = 7 = 0b111
   hcode = 29 = 0b11101
   29 & 7 = 0b101 = 5   (and 29 % 8 = 5 ✓)
   ```
   It keeps only the lowest bits of the hash, which is why a good hash
   function (one that mixes all bits) matters.

2. **Insert at the head** of that bucket's list: point the new node at the
   current head, then make it the new head. O(1), no walking.

---

## Lines 25–37: htabLookup, the pointer-to-pointer trick

```cpp
// Returns the slot pointing at the matching node, so the caller can unlink it.
HNode **HMap::htabLookup(HTab &htab, const HNode *key, EqFn eq) {
    if (htab.tab.empty()) {
        return nullptr;
    }
    HNode **from = &htab.tab[key->hcode & htab.mask];
    for (HNode *cur; (cur = *from) != nullptr; from = &cur->next) {
        if (cur->hcode == key->hcode && eq(cur, key)) {
            return from;
        }
    }
    return nullptr;
}
```

This is the trickiest function in the project. Take it slowly.

**The problem it solves.** To delete a node from a singly linked list in DSA,
you usually track `prev`:

```cpp
if (prev == nullptr) head = cur->next;   // special case: deleting the head
else prev->next = cur->next;
```

**The trick.** Instead of returning the node, return **the address of the
pointer that points to it**. That pointer is either the bucket slot
`tab[i]` (for the first node) or some earlier node's `next` field. Either
way, it's just an `HNode*` variable somewhere, and `from` is its address.

```
                from (start)                from (after 1 step)
                    │                            │
                    ▼                            ▼
 tab[3]: [ptr] ───► A{next: [ptr]} ───────► B{next: [ptr]} ───► null
```

To remove the node, whichever slot it is: `*from = (*from)->next;`. One
line, no special case for the head. (Linus Torvalds famously calls this
"good taste" in code.)

**Line by line:**
- **Line 27:** a table that's never been initialised has no buckets; nothing to find.
- **Line 30:** `from` = address of the bucket's head pointer.
- **Line 31:** a `for` loop with three parts:
  - init: declare `cur`;
  - condition: `cur = *from` (the node the slot points to), stop when it's `nullptr`;
  - step: `from = &cur->next` (move to the slot inside `cur`).
- **Line 32:** compare the stored hashes first (a cheap integer compare).
  Only if they match, call `eq` for the full key comparison (a string
  compare). Most non-matching nodes are rejected by the hash alone.
- **Line 33:** found: return the slot, not the node.

The caller gets the node itself with `*from`.

> **C++ note — `HNode **`:** a pointer to a pointer to an `HNode`. `*from`
> is an `HNode*` (the slot's value); `**from` would be the `HNode` itself.

---

## Lines 39–44: `htabDetach`

```cpp
HNode *HMap::htabDetach(HTab &htab, HNode **from) {
    HNode *node = *from;
    *from = node->next;
    htab.size--;
    return node;
}
```

Unlink the node that slot `from` points to, using the trick above:
1. Remember the node.
2. Make the slot skip it (point at the node's successor).
3. Decrease the count, return the unlinked node.

---

## Lines 46–51: `startResizing`

```cpp
void HMap::startResizing() {
    assert(older_.tab.empty());
    older_ = std::move(newer_);
    htabInit(newer_, (older_.mask + 1) * 2);
    migratePos_ = 0;
}
```

1. **Line 47:** sanity check: we must not start a resize while one is running.
2. **Line 48:** the full table becomes `older_`. `std::move` *transfers* the
   bucket vector's memory instead of copying it: O(1), no matter how big.
3. **Line 49:** create a fresh `newer_` with twice as many buckets.
   `mask + 1` is the old bucket count.
4. **Line 50:** start migrating from bucket 0.

Note that no nodes move yet. The work happens later in `helpRehashing`.

> **C++ note — `std::move`:** doesn't move anything by itself. It marks
> `newer_` as "you may steal from this". The assignment then takes the
> vector's internal pointer instead of copying all elements, leaving
> `newer_.tab` empty. We immediately re-initialise `newer_` anyway.

---

## Lines 53–67: `helpRehashing`, the incremental part

```cpp
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
```

Move up to 128 nodes from `older_` to `newer_`.

- **Line 55:** stop after 128 moves, or when `older_` is empty. If no resize
  is running, `older_.size` is 0 and the loop doesn't run at all, so calling
  this on every insert/pop is cheap.
- **Line 56:** look at the head slot of bucket `migratePos_`.
- **Lines 57–59:** bucket empty → go to the next bucket.
- **Line 61:** otherwise, detach the head node from `older_` and insert it
  into `newer_`. `newer_` computes the node's new bucket from its **stored**
  `hcode` (no rehashing of the key needed). Because we always take the
  head, the next loop iteration sees the next node of the same bucket.
- **Lines 64–66:** if everything has moved, replace `older_` with a fresh
  empty `HTab{}`, which frees the old bucket array. The resize is over.

**Worked example.** A table with 1024 buckets resizes when it reaches
1024 × 8 = 8192 nodes. `newer_` becomes 2048 buckets. Moving 8192 nodes at
128 per operation takes **64 operations**. Meanwhile, the next resize would
only trigger at 2048 × 8 = 16,384 nodes, 8192 inserts away. So a resize
always finishes long before the next one is needed.

**A subtle point for interviews:** skipping an empty bucket (line 58) isn't
counted as work. In a table with many empty buckets, one call could scan a
lot of them. Real Redis caps this too (it gives up after visiting 10 × n
empty buckets per step).

---

## Lines 69–79: destructor

```cpp
HMap::~HMap() {
    for (HTab *htab : {&newer_, &older_}) {
        for (HNode *node : htab->tab) {
            while (node) {
                HNode *next = node->next;
                deleter_(node);
                node = next;
            }
        }
    }
}
```

For both tables, for every bucket, walk the list and free each node.

**Line 73 matters:** save `next` *before* deleting the node. After
`deleter_(node)`, the node's memory is gone and reading `node->next` would be
a **use-after-free** bug.

The bucket vectors themselves are freed automatically when the `HTab`
members are destroyed (they're `std::vector`s).

> **C++ note — `for (HTab *htab : {&newer_, &older_})`:** the braces create
> a temporary list (`std::initializer_list`) of two pointers, and the loop
> runs once for each. A neat way to "do the same thing to these two
> variables" without copying code.

> **C++ note — `for (HNode *node : htab->tab)`:** copies each bucket's head
> pointer into a local `node`, which the `while` then walks.

---

## Lines 81–92: `insert`

```cpp
void HMap::insert(HNode *node) {
    if (newer_.tab.empty()) {
        htabInit(newer_, kInitSize);
    }
    htabInsert(newer_, node);

    bool resizing = !older_.tab.empty();
    if (!resizing && newer_.size >= (newer_.mask + 1) * kMaxLoadFactor) {
        startResizing();
    }
    helpRehashing();
}
```

1. **Lines 82–84:** lazy initialisation: the very first insert creates the
   4-bucket table. An unused `HMap` allocates nothing.
2. **Line 85:** insert into `newer_`.
3. **Lines 87–90:** if no resize is running and `newer_` has reached 8 nodes
   per bucket, start one. (If a resize is already running, wait for it to
   finish first; there are only ever two tables.)
4. **Line 91:** do a slice of migration work.

**Growth timeline:**

| Buckets | Resize triggers at | Migration takes |
|---|---|---|
| 4 | 32 nodes | 1 call (32 ≤ 128) |
| 8 | 64 | 1 call |
| 16 | 128 | 1 call |
| 32 | 256 | 2 calls |
| 1024 | 8192 | 64 calls |

Small tables finish resizing instantly; only big ones spread the work out.

---

## Lines 94–103: `lookup`

```cpp
HNode *HMap::lookup(const HNode *key) const {
    // htabLookup hands out a mutable slot for pop(); here we only read it.
    auto *self = const_cast<HMap *>(this);
    for (HTab *htab : {&self->newer_, &self->older_}) {
        if (HNode **from = htabLookup(*htab, key, eq_)) {
            return *from;
        }
    }
    return nullptr;
}
```

Search `newer_` first (most keys are there), then `older_`. Return the node
(`*from`), not the slot.

**Why the `const_cast`?** `lookup` is `const` (it promises not to change
the map), so inside it, `newer_` and `older_` are `const`. But `htabLookup`
takes a non-const `HTab&` because `pop` needs a writable slot. Rather than
write a second, read-only copy of `htabLookup`, we remove the `const` here.
It's safe because `lookup` only *reads* through the result.

> **C++ note — `if (HNode **from = ...)`:** declare a variable inside the
> `if` condition. The `if` checks whether it's non-null, and `from` only
> exists inside the `if`. Keeps the variable's scope tight.

> **C++ note — `this`:** inside a method, `this` is a pointer to the object
> the method was called on. In a `const` method it's a `const HMap*`.

---

## Lines 105–114: `pop`

```cpp
HNode *HMap::pop(const HNode *key) {
    for (HTab *htab : {&newer_, &older_}) {
        if (HNode **from = htabLookup(*htab, key, eq_)) {
            HNode *node = htabDetach(*htab, from);
            helpRehashing();
            return node;
        }
    }
    return nullptr;
}
```

Find the node in either table, unlink it with the slot trick, do a slice of
migration, and hand the node back. The **caller** now owns it and must
delete it.

Note `helpRehashing` only runs when something was actually removed.

---

## Lines 116–124: `hashBytes` (FNV-1a)

```cpp
// FNV-1a
uint64_t hashBytes(const uint8_t *data, size_t len) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (size_t i = 0; i < len; i++) {
        h ^= data[i];
        h *= 0x100000001b3ULL;
    }
    return h;
}
```

**FNV-1a** (Fowler–Noll–Vo) is a simple, fast, decent-quality hash:
1. Start from a fixed "offset basis" number.
2. For each byte: XOR the byte into the hash, then multiply by a special
   prime (the "FNV prime").

The XOR mixes each byte in; the multiplication spreads its effect across all
64 bits, so the low bits (the ones `& mask` uses) depend on every byte of
the key. `"key1"` and `"key2"` differ by one byte but end up in unrelated
buckets.

- `ULL` = "unsigned long long" literal suffix, so the constant is a 64-bit
  unsigned number.
- The multiplication **overflows** constantly. For unsigned integers in C++
  that's well-defined: it wraps around modulo 2⁶⁴, which is exactly what the
  algorithm wants. (For *signed* integers overflow is undefined behaviour,
  which is one reason hash code uses unsigned types.)

**Not cryptographic:** someone who knows the hash could choose keys that
all land in one bucket (a *hash-flooding* attack), turning O(1) into O(n).
Real Redis uses SipHash with a random secret key to prevent that.
