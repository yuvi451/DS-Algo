---
title: Progressive resizing
module: Our own hashtable
time: 40 min
---

:::goal
Teach `HashMap` to grow without ever pausing: when there are 8 nodes per
bucket on average, the current table becomes `older`, an empty `newer` twice
as big takes its place, and **every set and del moves up to 128 nodes**
across. After this lesson `hashtable.h`/`hashtable.cpp` are final.
:::

## The plan, in pictures

```text
normal:        newer = [4 buckets, 32 nodes]       older = (empty)
                        32 nodes / 4 buckets = 8 → time to grow!

start growing: newer = [8 buckets, 0 nodes]        older = [4 buckets, 32 nodes]
                                                            movePos = 0

each set/del moves ≤128 nodes, emptying older bucket by bucket from movePos:
               newer = [8 buckets, 20 nodes]       older = [4 buckets, 12 nodes]

done:          newer = [8 buckets, 32 nodes]       older = (freed)
```

While growing, a key may be in **either** table. That's why `get`, `set` and
`del` already check both!

## New constants and members

`hashtable.cpp`:

```cpp
const size_t INIT_SIZE = 4;        // buckets in a brand new table
const size_t MAX_LOAD = 8;         // grow when there are 8 nodes per bucket on average
const size_t MOVE_PER_CALL = 128;  // nodes moved per set/del while growing
```

`hashtable.h`, in `HashMap`:

```cpp
struct HashMap {
    Table newer;
    Table older;         // only non-empty while nodes are being moved
    size_t movePos = 0;  // next bucket of `older` to move

    // ... get, set, del, size as before ...
    void moveSomeNodes();
};
```

:::why Why grow at 8 per bucket, not 0.75 like `unordered_map`?
With chaining, a bucket holding several nodes is fine. A higher limit means
fewer, cheaper resizes and less memory for bucket arrays, at the cost of
slightly longer lists.
:::

## `moveSomeNodes`: a limited amount of work

```cpp
// Moves up to MOVE_PER_CALL nodes from `older` to `newer`.
void HashMap::moveSomeNodes() {
    size_t moved = 0;
    while (moved < MOVE_PER_CALL && older.size > 0) {
        Node *n = older.buckets[movePos];
        if (n == nullptr) {
            movePos++;  // this bucket is empty, go to the next one
            continue;
        }
        older.buckets[movePos] = n->next;  // take the first node of the bucket
        older.size--;
        addNode(newer, n);
        moved++;
    }
    if (older.size == 0 && !older.buckets.empty()) {
        older = Table();  // everything moved: free the old bucket array
    }
}
```

- `movePos` remembers which old bucket we're emptying, **between calls**.
- Each step takes the **first** node of that bucket (removing the first node
  of a list is easy: the bucket now starts at `n->next`), and `addNode` puts
  it in its new bucket in `newer`.
- At most 128 nodes per call, so the cost is limited no matter how big the
  table is.
- When nothing's left, `older = Table()` replaces it with a fresh empty table,
  which frees the old bucket array.

:::why Why don't we hash the keys again when moving them?
Each `Node` saved its `hash`. A node's bucket in the new table depends only
on that hash and the new mask, which `addNode` already handles. That's why
`Node` keeps the hash around.
:::

## Hooking it into `set` and `del`

`set` checks, after adding a new node, whether it's time to start growing:

```cpp
    if (newer.buckets.empty()) initTable(newer, INIT_SIZE);
    addNode(newer, new Node{key, val, hash, nullptr});

    // Too full? Start growing: the full table becomes `older`, and an empty
    // table twice as big becomes `newer`. swap() just trades the two tables.
    bool growing = !older.buckets.empty();
    if (!growing && newer.size >= newer.buckets.size() * MAX_LOAD) {
        swap(older, newer);
        initTable(newer, older.buckets.size() * 2);
        movePos = 0;
    }
    moveSomeNodes();
}
```

and `del` helps too, after deleting:

```cpp
    delete n;
    moveSomeNodes();
    return true;
```

- New keys always go into `newer`.
- We only start growing when we aren't already growing.
- `swap(older, newer)` trades the contents of the two tables instantly. It
  doesn't copy the nodes, it just swaps the insides. Then `newer` is
  re-created with twice as many buckets.
- `moveSomeNodes` returns immediately when `older` is empty, so calling it
  every time is cheap.
- `get` stays read-only and doesn't help. It already checks both tables.

:::quiz Can the new table fill up again before the old one is empty?
In practice no. The new table has **2×** the buckets, so it reaches its limit
only after roughly as many new keys again as there were in total. Each of
those `set`s moved up to 128 nodes, so the old table emptied long before.
Even so, the `!growing` check makes sure we never start a second resize while
one is running.
:::

## The big test

```cpp
// Enough keys to make the table grow several times. Checks that every key is
// still found while nodes are halfway between the two tables.
void testGrowing() {
    const int N = 5000;
    HashMap m;
    bool sawGrowing = false;
    for (int i = 0; i < N; i++) {
        m.set("key" + to_string(i), "val" + to_string(i));
        if (!m.older.buckets.empty()) sawGrowing = true;
    }
    assert(sawGrowing);
    ...
}
```

5,000 keys pass through tables of 4 → 8 → 16 → … → 1024 buckets.
`sawGrowing` proves we actually caught it halfway through a move. Every key
must still be findable, and after deleting the even keys exactly the odd ones
must remain.

:::task Finish the hashtable
1. Add the constants, `movePos` and `moveSomeNodes` (and update the `older`
   comment to `// only non-empty while nodes are being moved`).
2. Write `moveSomeNodes`, and update `set` and `del`.
3. Add `testGrowing` to the tests and call it last in `main`.

```bash
$ c++ -std=c++17 -Wall test/test_hashtable.cpp src/hashtable.cpp -o build/test_hashtable
$ build/test_hashtable
```
:::

```output
testSetAndGet: OK
testDel: OK
testGrowing: OK
All hashtable tests passed.
```

:::solution These are the final project files
@include ../src/hashtable.h
@include ../src/hashtable.cpp
@include ../test/test_hashtable.cpp
:::

:::recap
- Grow when `size >= buckets × 8`: `swap(older, newer)`, then a new `newer` with 2× the buckets.
- Each set/del moves ≤ 128 nodes starting at `movePos`. No call ever pays for the whole resize.
- Lookups check both tables. New keys always go to `newer`.
- 🎉 **The hashtable is complete.** Next: plug it into the server.
:::
