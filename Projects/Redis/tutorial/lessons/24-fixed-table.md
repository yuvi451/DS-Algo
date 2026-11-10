---
title: The chaining hashtable (fixed size first)
module: Our own hashtable
time: 60 min
---

:::goal
Build `HashMap` without growing: a table of buckets, each bucket a linked
list of `Node`s. Write `get`, `set` and `del`, using the linked-list skills
from the pointers lesson. Then unit-test it.
:::

## The data: `Node`, `Table`, `HashMap`

Add this to `src/hashtable.h` (it also needs `#include <vector>`):

```cpp
// One key-value pair. Pairs that land in the same bucket form a linked list.
struct Node {
    string key;
    string val;
    uint64_t hash;
    Node *next;
};

// An array of buckets. Its size is always a power of two, so the bucket for
// a hash is (hash & mask), which is the same as hash % size but faster.
struct Table {
    vector<Node *> buckets;
    size_t mask = 0;
    size_t size = 0;  // number of nodes in this table
};

// Chained hashtable. For now it never grows (that's the next lesson).
struct HashMap {
    Table newer;
    Table older;  // stays empty until the next lesson adds growing

    bool get(const string &key, string &val);  // false if key is missing
    void set(const string &key, const string &val);
    bool del(const string &key);  // false if key was missing
    size_t size();
};
```

```text
Table (4 buckets, mask = 3):
 buckets[0] ─► [cat|…] ─► [emu|…] ─► nullptr
 buckets[1] ─► nullptr
 buckets[2] ─► [foo|…] ─► nullptr
 buckets[3] ─► [ant|…] ─► [bee|…] ─► nullptr
```

There are three levels:

- **`Node`**: one key-value pair, plus its `hash` (saved so we never have to
  hash the key again) and `next` (the next node in the same bucket).
- **`Table`**: one array of buckets. Each bucket holds a pointer to the first
  node of its list, or `nullptr` if it's empty.
- **`HashMap`**: what the server uses. It holds **two** tables, `newer` and
  `older`, ready for growing next lesson. Today `older` is always empty, but
  `get` and `del` already check it.

## Small helpers

These go at the top of `hashtable.cpp`, after `hashString`. Each one works on
one `Table`.

```cpp
const size_t INIT_SIZE = 4;  // buckets in a brand new table

void initTable(Table &t, size_t n) {
    t.buckets.assign(n, nullptr);  // n empty buckets
    t.mask = n - 1;
    t.size = 0;
}

// Push node onto the front of its bucket's list.
void addNode(Table &t, Node *node) {
    size_t i = node->hash & t.mask;
    node->next = t.buckets[i];
    t.buckets[i] = node;
    t.size++;
}
```

```text
before:  buckets[i] ──► A ──► B ──► nullptr
after:   buckets[i] ──► N ──► A ──► B ──► nullptr
```

Adding at the **front** of the list is O(1): no need to walk to the end.

```cpp
Node *findNode(Table &t, const string &key, uint64_t hash) {
    if (t.buckets.empty()) return nullptr;
    for (Node *n = t.buckets[hash & t.mask]; n != nullptr; n = n->next) {
        if (n->hash == hash && n->key == key) return n;
    }
    return nullptr;
}
```

`findNode` walks one bucket's list. `t.buckets.empty()` is true for a table
that was never set up (like `older` today).

:::why Why compare `hash` before `key`?
Comparing two numbers is nearly free, while comparing two long strings is
not. Different hashes guarantee different keys, so most non-matches are
rejected without ever comparing strings.
:::

Removing is the linked-list removal from the pointers lesson. We walk with a
`prev` pointer so we can make the previous node point past the one we remove:

```cpp
// Unlinks the node with this key from t and returns it, or nullptr.
Node *removeNode(Table &t, const string &key, uint64_t hash) {
    if (t.buckets.empty()) return nullptr;
    size_t i = hash & t.mask;
    Node *prev = nullptr;
    Node *n = t.buckets[i];
    while (n != nullptr) {
        if (n->hash == hash && n->key == key) {
            if (prev == nullptr) {
                t.buckets[i] = n->next;  // it was the first node
            } else {
                prev->next = n->next;
            }
            t.size--;
            return n;
        }
        prev = n;
        n = n->next;
    }
    return nullptr;
}
```

```text
removing B (prev = A):
 before:  buckets[i] ─► A ─► B ─► C
 after:   buckets[i] ─► A ──────► C
```

## The `HashMap` methods

```cpp
bool HashMap::get(const string &key, string &val) {
    uint64_t hash = hashString(key);
    Node *n = findNode(newer, key, hash);
    if (n == nullptr) n = findNode(older, key, hash);
    if (n == nullptr) return false;
    val = n->val;
    return true;
}

void HashMap::set(const string &key, const string &val) {
    uint64_t hash = hashString(key);
    Node *n = findNode(newer, key, hash);
    if (n == nullptr) n = findNode(older, key, hash);
    if (n != nullptr) {
        n->val = val;  // key exists: overwrite
        return;
    }

    if (newer.buckets.empty()) initTable(newer, INIT_SIZE);
    addNode(newer, new Node{key, val, hash, nullptr});
}

bool HashMap::del(const string &key) {
    uint64_t hash = hashString(key);
    Node *n = removeNode(newer, key, hash);
    if (n == nullptr) n = removeNode(older, key, hash);
    if (n == nullptr) return false;
    delete n;
    return true;
}

size_t HashMap::size() {
    return newer.size + older.size;
}
```

- Each method hashes the key **once**, then looks in `newer`, then `older`.
- `set` first checks whether the key exists. If so, it just changes the
  value. Otherwise it creates the table on first use, then adds a brand-new
  node made with `new`.
- `del` unlinks the node, then `delete`s it, since we made it with `new`.

## Tests

```cpp
void testSetAndGet() {
    HashMap m;
    string val;
    assert(!m.get("name", val));
    m.set("name", "redis");
    assert(m.get("name", val));
    assert(val == "redis");
    m.set("name", "microredis");  // overwrite
    assert(m.get("name", val));
    assert(val == "microredis");
    assert(m.size() == 1);
    cout << "testSetAndGet: OK" << endl;
}
```

:::task Build the fixed-size HashMap and test it
1. Complete `src/hashtable.h` (add `#include <vector>`, `Node`, `Table` and
   `HashMap`; keep `hashString` at the bottom).
2. Complete `src/hashtable.cpp` with everything above.
3. Create `test/test_hashtable.cpp`:

@include code/f-hashtable/s2/test/test_hashtable.cpp

```bash
$ c++ -std=c++17 -Wall test/test_hashtable.cpp src/hashtable.cpp -o build/test_hashtable
$ build/test_hashtable
```
:::

```output
testSetAndGet: OK
testDel: OK
All hashtable tests passed.
```

:::solution
@include code/f-hashtable/s2/src/hashtable.h
@include code/f-hashtable/s2/src/hashtable.cpp
:::

:::quiz After setting 100 keys in this fixed table, what's the average list length?
The table never grows: 4 buckets, so about **25** nodes per list. Every
lookup walks ~25 nodes. That's O(n) behavior, which is exactly why we add
growing next.
:::

:::recap
- `Node` = key + value + saved hash + `next`. `Table` = buckets + mask + size. `HashMap` = two tables.
- `addNode` pushes onto the front of a bucket's list: O(1).
- `findNode` walks one list. `removeNode` unlinks with a `prev` pointer (the first node is the special case).
- `set` overwrites or adds a `new Node`. `del` unlinks and `delete`s.
:::
