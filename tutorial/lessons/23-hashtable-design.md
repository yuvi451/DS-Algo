---
title: Why build our own hashtable? (and hashing bytes)
module: Our own hashtable
time: 45 min
---

:::goal
Understand why Redis can't just use `unordered_map`: the problem is
**worst-case latency** when the table resizes. Review chaining hashtables
from DSA, learn the power-of-two "mask" trick, and write the hash function
our table will use: **FNV-1a**.
:::

## A hashtable in three lines

From DSA you know the idea: turn a key into a number (its **hash**), use that
number to pick a **bucket**, and keep a small list in each bucket for keys
that land in the same place (**collisions**):

```cpp
vector<vector<pair<string, string>>> m(N);            // N buckets
m[hash(key) % N].push_back({key, val});               // insert
for (auto &p : m[hash(key) % N]) if (p.first == key)  // lookup
```

```text
bucket 0: → ("cat", …) → ("emu", …)
bucket 1: (empty)
bucket 2: → ("foo", …)
bucket 3: → ("ant", …) → ("bee", …) → ("cow", …)
```

This is a **chaining** hashtable: each bucket holds a chain of entries. The
other family, **open addressing**, stores entries directly in the array and
probes for the next free slot on collision. We use chaining, like
`unordered_map` and real Redis. Our chains will be the linked lists from the
pointers lesson.

## Load factor and resizing

**Load factor** = number of keys / number of buckets = average chain length.
Lookups cost O(1 + load factor). To keep them fast, when the load factor gets
too high we create a **bigger** table (usually 2× the buckets) and move every
key into it (**rehashing**). Like `vector` doubling, this makes the
*average* insert O(1).

## The problem: one insert that takes a whole second

*Average* O(1) hides an ugly *worst case*. The insert that triggers a resize
must move **every** key: O(n) in one go.

```text
insert, insert, insert, … insert (triggers resize: moves 50 million keys!) …
  1µs    1µs     1µs          ~1–2 seconds of the server doing nothing else
```

For a library in a single program, a rare pause is fine. For **Redis**,
serving thousands of clients from one thread, a 1-second pause means
**every** client times out at the same moment. Redis cares about the
**worst-case latency** of every operation, not just the average.

:::why Can't we just pick a big table up front?
You don't know how many keys users will store, and a huge empty table wastes
memory. Resizing is necessary, so we need to make it **gradual**.
:::

## The fix: progressive rehashing (preview)

Instead of moving all keys at once:

1. When the table is too full, allocate the bigger table, but **don't move
   anything yet**. Keep the old table around.
2. On every insert or delete, move **a small fixed number** of keys
   (128) from the old table to the new one.
3. Lookups check **both** tables until the old one is empty.

Each operation does a little extra, constant work, so **no single operation
is ever slow**. We'll build this in two lessons' time.

## The power-of-two trick: `hash & mask`

`hash % N` needs division, one of the slowest arithmetic instructions. If
`N` is a **power of two**, `hash % N` equals `hash & (N - 1)`: just keep the
lowest bits.

```text
N = 8          → N - 1 = 7 = 0b0111   (the "mask")
hash = 0b1101_1010 (218)
hash & 0b0111      = 0b010 = 2        → bucket 2  (and 218 % 8 = 2 ✓)
```

Our table sizes are always 4, 8, 16, 32, …, and each table stores
`mask = size - 1`.

## The hash function: FNV-1a

A good hash function spreads keys evenly over the buckets, even when the keys
look alike (`key1`, `key2`, …). We use **FNV-1a**, a classic, tiny, fast hash
for hashtables:

```cpp
// FNV-1a: a simple, fast hash for strings.
uint64_t hashString(const string &s) {
    uint64_t h = 0xcbf29ce484222325ULL;   // "offset basis": a fixed starting value
    for (char c : s) {
        h ^= (unsigned char)c;            // mix in one byte (XOR)
        h *= 0x100000001b3ULL;            // multiply by the "FNV prime" to spread it out
    }
    return h;
}
```

- `^` is **XOR**: flips the bits of `h` wherever the byte has a 1 bit.
- The multiplication scrambles those changes across all 64 bits, so a
  one-letter difference (`foo` vs `fop`) gives completely different hashes.
- The two magic constants come from the FNV specification. You don't derive
  them, you look them up.
- `(unsigned char)c` treats the char as a byte from 0 to 255. (A plain `char`
  can be negative on some machines, which would mix in the wrong bits.)

:::cpp `ULL` suffix and overflow
`0xcbf29ce484222325ULL` means "this literal is an `unsigned long long`"
(64 bits), so the compiler doesn't treat it as a smaller type. The
multiplication overflows 64 bits constantly, and that's fine and intended:
for **unsigned** types C++ guarantees overflow wraps around (mod 2⁶⁴). For
*signed* types overflow is undefined behavior. That's one more reason hashes
use unsigned types.
:::

:::why Why not use a cryptographic hash like SHA-256?
Crypto hashes are designed to be hard to reverse, which makes them slow. A
hashtable needs **speed** and **good spreading**, nothing more. FNV-1a does a
few cheap operations per byte. (Never use FNV for passwords or security, though.)
:::

:::task Start hashtable.h / hashtable.cpp with the hash function
1. Create `src/hashtable.h` with `#pragma once`, includes `<cstdint>` and
   `<string>`, `using namespace std;`, and the declaration
   `uint64_t hashString(const string &s);`
2. Create `src/hashtable.cpp` that includes `"hashtable.h"` and defines
   `hashString`.
3. Create `scratch/fnv.cpp` that prints the hash of a few strings, and which
   of 8 buckets each lands in:

@include code/f-hashtable/fnv.cpp title=scratch/fnv.cpp

```bash
$ c++ -std=c++17 -Wall scratch/fnv.cpp src/hashtable.cpp -o build/fnv
$ build/fnv
```
:::

```output
hash("") = 14695981039346656037  -> bucket 5 of 8
hash("a") = 12638187200555641996  -> bucket 4 of 8
hash("foo") = 15902901984413996407  -> bucket 7 of 8
hash("fop") = 15902907481972137462  -> bucket 6 of 8
```

If your hashes match these exactly, your FNV-1a is correct. Notice `""` gives
back the offset basis (`0xcbf29ce484222325`) unchanged, since there were no
bytes to mix in. And `foo`/`fop` differ in one letter, but their hashes
differ in many digits.

:::solution
@include code/f-hashtable/s1/src/hashtable.h
@include code/f-hashtable/s1/src/hashtable.cpp
:::

:::recap
- Chaining hashtable = array of buckets, each a chain of entries.
- Resizing all at once causes **latency spikes**. Redis resizes **progressively**.
- Power-of-two sizes: `bucket = hash & mask` with `mask = size - 1`.
- FNV-1a: start at the offset basis; per byte, XOR then multiply by the prime.
:::
