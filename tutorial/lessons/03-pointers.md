---
title: Pointers, references and linked lists
module: C++ toolkit
time: 40 min
---

:::goal
Our hashtable is built out of **linked lists**, and linked lists are built
out of **pointers**. This lesson gives you a solid mental model of pointers,
`->`, `nullptr`, references, `new`/`delete`, and how to add and remove nodes
in a linked list.
:::

## A pointer is just an address

Every variable lives at some position in memory. That position is its
**address**. A **pointer** is a variable that stores an address.

```cpp
int score = 42;
int *p = &score;   // p holds the address of score
```

```text
        score                         p
     ┌─────────┐                ┌──────────────┐
     │   42    │ ◄───────────── │  0x7ff5a010  │
     └─────────┘                └──────────────┘
   address 0x7ff5a010
```

A few symbols do all the work:

| Syntax | Read it as | Example |
|---|---|---|
| `int *p` (in a declaration) | "`p` is a pointer to an `int`" | `int *p = &score;` |
| `&x` | "the address of `x`" | `&score` |
| `*p` (in an expression) | "the thing `p` points at" | `*p = 50;` changes `score` to 50 |
| `p->field` | shorthand for `(*p).field` | `conn->fd` |
| `nullptr` | "points at nothing" | `Node *next = nullptr;` |

:::analogy
A variable is a house. Its address is the street address. A pointer is a
piece of paper with an address written on it. `*p` means "go to the address
written on the paper and look inside the house".
:::

## References: another name for a variable

In DSA you've likely written `void dfs(vector<int> &adj)`. That `&` in a
**type** makes a **reference**: another name for an existing variable.

```cpp
void addTen(int &x) { x += 10; }   // x IS the caller's variable

int score = 5;
addTen(score);   // score is now 15
```

We use references a lot for **output parameters**: a function that returns
`bool` (did it work?) and writes its real result into a `&` parameter:

```cpp
bool get(const string &key, string &val);   // fills val if the key exists

string val;
if (db.get("name", val)) cout << val << endl;
```

:::cpp `const string &`: the "read-only, no copy" argument
`void print(const string &s)` passes the string **without copying it**
(a reference) and **without allowing changes** (`const`). You'll see
`const string &` and `const vector<string> &` everywhere in our code.
:::

## `new` and `delete`

Normally, local variables vanish when their function returns. `new` creates an
object that lives until you explicitly `delete` it:

```cpp
Node *n = new Node{1, nullptr};   // lives on the "heap" until...
delete n;                         // ...you free it
```

`new` gives you back a **pointer** to the new object. Our server uses `new`
for every key-value pair and every client connection, and `delete` when they
go away.

## Linked lists

A linked list is a chain of nodes where each node points at the next one. The
last one points at `nullptr`:

```cpp
struct Node {
    int val;
    Node *next;
};
```

```text
head ─► [1 | next ●]─► [2 | next ●]─► [3 | next = nullptr]
```

Walking the list:

```cpp
for (Node *n = head; n != nullptr; n = n->next) {
    cout << n->val;
}
```

**Removing** a node means making the node *before* it point *past* it, then
freeing it:

```text
before:  head ─► [1] ─► [2] ─► [3]
after:   head ─► [1] ──────────► [3]        (then delete [2])
```

```cpp
Node *middle = head->next;   // node 2
head->next = middle->next;   // 1 now points at 3
delete middle;
```

Our hashtable keeps one linked list per bucket and does exactly these two
things: walk a list to find a key, and unlink a node to delete a key.

:::task Practice pointers and lists
Write `scratch/pointers.cpp` with:

1. `void addTen(int &x)`, which adds 10 to the caller's variable.
2. `struct Node { int val; Node *next; };`
3. In `main`:
   - make `int score = 5;`, a pointer `p` to it, set `*p = 7;`, print `score`
   - call `addTen(score)` and print it
   - build the list `1 → 2 → 3` with `new`, print it
   - remove node 2 as shown above, and print the list again

```bash
$ c++ -std=c++17 -Wall scratch/pointers.cpp -o build/pointers
$ build/pointers
```
:::

```output
score: 7
after addTen: 17
list: 1 2 3
after removing 2: 1 3
```

:::hint Hint: building the list
`new Node{1, nullptr}` makes a node with `val = 1` and `next = nullptr`.
```cpp
Node *head = new Node{1, nullptr};
head->next = new Node{2, nullptr};
head->next->next = new Node{3, nullptr};
```
:::

:::solution
@include code/a-basics/pointers.cpp title=scratch/pointers.cpp
:::

:::quiz How would you remove the *first* node of a list?
There's no node before it, so you change `head` itself:
`Node *first = head; head = head->next; delete first;`. Our hashtable's
delete has exactly these two cases: "it's the first node in the bucket" and
"it's after some other node".
:::

:::recap
- `&x` = address of x. `*p` = what p points at. `p->f` = `(*p).f`. `nullptr` = nothing.
- References (`T &`) are other names for a variable. `const T &` means "read-only, no copy".
- A function can return `bool` and fill in a `&` output parameter.
- `new` makes an object that lives until `delete`.
- A linked list: walk with `n = n->next`, remove by pointing the previous node past it.
:::
