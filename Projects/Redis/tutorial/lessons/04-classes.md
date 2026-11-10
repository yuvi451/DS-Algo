---
title: Structs with functions inside
module: C++ toolkit
time: 25 min
---

:::goal
Our server has a `Conn` (one per client) and a `HashMap` (the database). Both
are plain `struct`s: some variables, plus a few functions that work on them.
This lesson covers everything about structs that the project uses, and
nothing more.
:::

## From DSA `struct` to a struct with functions

You've probably written a DSA `struct`:

```cpp
struct Edge {
    int to;
    int weight;
};
```

A struct can also hold **functions** (called *methods*). Inside a method, the
struct's own variables are available directly:

```cpp
struct Counter {
    string name;
    int count = 0;          // every new Counter starts at 0

    void add() { count++; }
    void print() { cout << name << ": " << count << endl; }
};

Counter a;
a.name = "a";
a.add();
a.print();                  // a: 1
```

- `int count = 0;` gives the variable a **default value**. Every new
  `Counter` starts with `count` at 0.
- `a.add()` calls `add` on the object `a`, so `count++` changes `a.count`.

:::cpp What about `class`, `private`, constructors…?
C++ has a lot more: `class`, `public`/`private`, constructors, destructors,
and so on. They're useful in big programs, but **this project doesn't need
them**. A plain `struct` with default values does everything we need.
:::

## Writing a method outside the struct

Short methods can live inside the struct. For longer ones, we only **declare**
them inside, and write the body outside using `StructName::`:

```cpp
struct HashMap {
    bool get(const string &key, string &val);   // just the declaration
};

bool HashMap::get(const string &key, string &val) {   // the body
    // ...
}
```

`HashMap::get` means "the `get` that belongs to `HashMap`". You'll see this
in `hashtable.cpp`.

## Structs and `new`

Structs work with `new` like anything else. Through a pointer, use `->`:

```cpp
Counter *b = new Counter();
b->name = "b";
b->add();
delete b;
```

Our server does exactly this for every connected client: `new Conn()` when a
client connects, `delete conn` when it leaves.

:::task Write a struct
Write `scratch/classes.cpp` with the `Counter` struct above, then in `main`:

1. Make a `Counter a` named `"a"`, call `add()` twice, then `print()`.
2. Make a `Counter *b` with `new`, named `"b"`, call `add()` once, `print()`,
   then `delete` it.

```bash
$ c++ -std=c++17 -Wall scratch/classes.cpp -o build/classes
$ build/classes
```
:::

```output
a: 2
b: 1
```

:::solution
@include code/a-basics/classes.cpp title=scratch/classes.cpp
:::

:::quiz What does `Counter c;` print if you call `c.print()` straight away?
`: 0`. `name` is an empty string, and `count` starts at its default value 0.
:::

:::recap
- A `struct` can hold variables (with default values) and methods.
- Methods can be written inside the struct, or outside as `StructName::method`.
- `new StructName()` gives a pointer. Use `->` to reach its members, and `delete` when done.
:::
