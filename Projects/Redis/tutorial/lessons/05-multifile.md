---
title: Programs made of several files
module: C++ toolkit
time: 25 min
---

:::goal
DSA solutions are one file. Our project has four `.cpp` files plus two
headers, and the client and server **share** the protocol code. Learn how
headers and multi-file compiling work.
:::

## Why split code into files?

The server and the client both need to encode and decode messages. If we
copy-pasted that code into both, a fix in one place would be forgotten in the
other. Instead:

```text
             protocol.h   ◄── "here's what exists" (declarations)
             protocol.cpp ◄── "here's how it works" (definitions)
               ▲      ▲
 server.cpp ───┘      └─── client.cpp      both #include "protocol.h"
```

## Declaration vs definition

- A **declaration** says *"this exists, and here's its shape"*:
  `string greet(const string &name);` (note the `;` and no body).
- A **definition** provides the body: `string greet(...) { ... }`.

A **header file** (`.h`) holds declarations. A **source file** (`.cpp`) holds
definitions. Other files `#include` the header so they know what they can
call.

:::cpp What `#include` actually does
`#include "greet.h"` literally **pastes the contents of `greet.h`** at that
spot before compiling. Angle brackets `<iostream>` search the system's
standard headers. Quotes `"greet.h"` search next to your file first. That's
why our own headers use quotes.
:::

## `#pragma once`

If a header gets pasted twice into the same file (for example, two headers
that both include it), everything in it would be declared twice, which can be
an error. Putting `#pragma once` as the first line of a header tells the
compiler "only paste this file once". Every header in our project starts with
it.

## `using namespace std;`

Everything in the C++ standard library lives in a **namespace** called
`std`, which is why its full names are `std::vector`, `std::string`,
`std::cout`. Like in DSA, we write `using namespace std;` once so we can just
write `vector`, `string`, `cout`.

Our headers include it too, so every file that includes `protocol.h` or
`hashtable.h` gets it automatically.

:::warn The one place it bites us: `bind`
The operating system has a function `bind()` (you'll meet it in the sockets
lesson), and the standard library *also* has an unrelated `std::bind`. With
`using namespace std;`, plain `bind(...)` may pick the wrong one and give a
long, confusing error. The fix is to write **`::bind(...)`**. The `::` in
front means "the one that is **not** inside any namespace", which is the
operating system's.

You'll see `::bind` in our servers. That's the only place this matters.
:::

## Compiling several files into one program

List all the `.cpp` files in one command. **Never list `.h` files.** They
are pulled in by `#include`.

```bash
$ c++ -std=c++17 -Wall scratch/main.cpp scratch/greet.cpp -o build/greet
```

```text
 main.cpp  ──compile──►  main.o  ─┐
                                  ├──link──►  build/greet
 greet.cpp ──compile──►  greet.o ─┘
```

Each `.cpp` is compiled separately. Then the **linker** connects the call to
`greet()` in `main.o` with its body in `greet.o`.

:::warn The two classic errors
- `use of undeclared identifier 'greet'`: you forgot to `#include "greet.h"`.
  The *compiler* doesn't know the function exists.
- `Undefined symbols ... greet` (macOS) or `undefined reference to greet`
  (Linux): you forgot to put `greet.cpp` in the compile command. The
  *linker* can't find the body.
:::

:::task Build a three-file program
Create these files in `scratch/`:

1. `greet.h`: `#pragma once`, `#include <string>`, `using namespace std;`, and
   the declaration `string greet(const string &name);`
2. `greet.cpp`: include `"greet.h"` and define `greet` to return
   `"hello, " + name + "!"`.
3. `main.cpp`: include `"greet.h"` and print `greet("redis")` with `cout`.

```bash
$ c++ -std=c++17 -Wall scratch/main.cpp scratch/greet.cpp -o build/greet
$ build/greet
```
:::

```output
hello, redis!
```

:::solution
@include code/a-basics/greet.h title=scratch/greet.h
@include code/a-basics/greet.cpp title=scratch/greet.cpp
@include code/a-basics/main.cpp title=scratch/main.cpp
:::

:::quiz Leave `scratch/greet.cpp` out of the compile command. Which error do you get, and from whom?
A **linker** error (`Undefined symbols … greet`). `main.cpp` compiled fine
because the header declared `greet`, but no compiled file contains its body.
:::

:::recap
- Headers (`.h`) declare, sources (`.cpp`) define. `#include "x.h"` pastes the header in.
- `#pragma once` at the top of every header.
- `using namespace std;` like in DSA. Write `::bind` for the operating system's `bind`.
- Compile **all** `.cpp` files together. Missing one gives a *linker* error.
:::

You now have every C++ tool needed to start networking. Anything else (a
cast, an `enum`) is explained in the lesson where we first need it.
