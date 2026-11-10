---
title: Welcome! What we're going to build
module: Start here
time: 10 min
---

:::goal
By the end of this course you will have written, line by line, a small
**Redis-like database server** in C++, plus a client that talks to it over
the network. You'll understand every single line, and why it is there.
:::

## What is Redis?

Imagine an `unordered_map<string, string>` from your DSA
practice. Now imagine that this map lives inside a program that runs all the
time, and *other programs* can ask it questions over the network:

- "Please store `name` → `alice`" (**set**)
- "What is stored under `name`?" (**get**)
- "Forget `name`" (**del**)

That's Redis at its heart: **a hashmap you talk to over the network.** Big
companies put Redis in front of slow databases as a *cache*. Memory is much
faster than disk, so answering from Redis is very fast.

:::analogy
Think of Redis as a **librarian behind a counter**. You (the client) walk up
and say "give me the book called `foo`". The librarian (the server) looks in
their shelves (the hashmap) and hands it over, or says "we don't have it".
Many people can queue at the counter, and the librarian serves them all.
:::

## What you'll have at the end

You'll run the server in one terminal window:

```bash
$ build/server
listening on 127.0.0.1:1234
```

…and talk to it from another terminal window:

```bash
$ build/client set foo bar
OK
$ build/client get foo
bar
$ build/client del foo
OK
$ build/client get foo
(nil)
```

Under the hood, your server will:

- speak **TCP** over the network using raw **sockets**, the same API real Redis uses
- use its own **binary protocol** to turn commands into bytes and back again
- serve **hundreds of clients at the same time with a single thread**, using an
  **event loop** built on `poll()`
- store data in **its own hashtable**, written from scratch, which grows a
  little at a time so it never freezes
- handle about **180,000 requests per second** on a laptop

The finished project is about 800 lines of C++, tests included. Every one of
them is explained in this course.

## Plain, beginner-friendly C++

This course is about **how Redis works**, not about mastering every corner
of C++. So the code is written the way you write DSA solutions:

- `using namespace std;`, `cout`, `string`, `vector`
- plain `struct`s with a few functions inside, and `new`/`delete`
- functions that return `bool` (worked or not) and fill in a `&` parameter

No smart pointers, no templates, no clever tricks. When a line needs
something unusual (a cast, an operating-system call), the lesson says why.

## How every lesson works

This course copies the style of hands-on platforms like CodeCrafters and the
book *Build Your Own Redis*. Every lesson follows the same rhythm:

| Step | What happens |
|---|---|
| 1. **Concept** | A plain-English explanation of the idea, usually with an analogy and a diagram. No jargon without explaining it. |
| 2. **Syntax** | Every C++ feature or system function we need, explained with *why* it looks the way it does. |
| 3. **Your turn** | A coding task (red box). You write the code yourself. |
| 4. **Expected output** | The exact output you should see (green box), so you know if you got it right. |
| 5. **Hints → Solution** | Stuck? Open a hint. Still stuck? Reveal the full solution. No shame, just learn from it. |

You'll also see these boxes:

:::why Why do these boxes exist?
Yellow boxes answer the *"but why?"* questions that beginners usually have
and tutorials usually skip.
:::

:::cpp C++ syntax boxes
Purple boxes explain C++ you may not have met in DSA: pointers, `new` and
`delete`, casts, and so on.
:::

:::net Networking boxes
Blue boxes explain networking ideas: ports, TCP, sockets, byte order.
:::

:::warn Common mistakes
Red boxes warn you about a common mistake *before* you make it.
:::

:::quiz Can I check my understanding?
Yes! Blue "quiz" questions hide their answer until you click them. Try to
answer in your head first.
:::

## The roadmap

| Part | You will learn | You will build |
|---|---|---|
| 0. Start here | Setting up a compiler and terminal | A hello-world |
| 1. C++ toolkit | Bytes, pointers, structs, multi-file programs | Small practice programs |
| 2. How networks work | IP, ports, TCP, file descriptors, sockets | A program that accepts connections |
| 3. First server & client | `read`/`write` over the network, byte streams | A "hello → world" server and client |
| 4. The protocol | Turning commands into bytes and back | `protocol.h` / `protocol.cpp` + tests |
| 5. The event-loop server | Non-blocking I/O, `poll()`, buffering | `server.cpp` and `client.cpp` |
| 6. Our own hashtable | Hashing, chaining, progressive resizing | `hashtable.h` / `hashtable.cpp` + tests |
| 7. Ship it | Makefiles, integration tests, benchmarks | `Makefile`, test script, load tester |

## What you need to know already

- Basic C++ the way it's used in DSA: variables, `if`/`for`/`while`,
  functions, `vector`, `string`, maybe a `struct`.
- That's it. **No networking or Redis knowledge is assumed.** We build up
  everything else from zero, including pointers.

:::warn Don't skip the "Your turn" boxes
Reading code feels like understanding it, but writing it is how you actually
learn it. Type the code yourself instead of copy-pasting. You'll make typos,
the compiler will complain, and fixing those errors is where most of the
learning happens.
:::

Your progress is saved in your browser. Use the sidebar, the **Next →**
button, or the **←/→ arrow keys** to move between lessons. Ready? Let's set
up your workspace.
