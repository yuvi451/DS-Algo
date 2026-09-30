# Code Breakdown

A line-by-line walkthrough of MicroRedis, written for someone who knows C++
from DSA but hasn't done systems or network programming.

Line numbers match commit `0ebeebd`. If you edit the code later, the line
numbers may drift but the explanations still apply.

## Reading order

Read top to bottom the first time. Each file assumes you've read the ones
above it.

| # | File | What you'll learn |
|---|---|---|
| 01 | [networking-refresher.md](01-networking-refresher.md) | Everything about TCP, sockets and event loops you need for this project |
| 02 | [protocol.h.md](02-protocol.h.md) | The message format clients and server agree on |
| 03 | [protocol.cpp.md](03-protocol.cpp.md) | Encoding/decoding bytes, framing, blocking socket I/O |
| 04 | [hashtable.h.md](04-hashtable.h.md) | The hashtable's public interface and intrusive nodes |
| 05 | [hashtable.cpp.md](05-hashtable.cpp.md) | Chaining, pointer-to-pointer tricks, incremental resizing |
| 06 | [server.cpp.md](06-server.cpp.md) | The key-value store and the `poll()` event loop (the heart of the project) |
| 07 | [client.cpp.md](07-client.cpp.md) | The command-line client |
| 08 | [loadtest.cpp.md](08-loadtest.cpp.md) | The benchmark: threads, timing, percentiles |
| 09 | [test_hashtable.cpp.md](09-test_hashtable.cpp.md) | Hashtable unit tests |
| 10 | [test_protocol.cpp.md](10-test_protocol.cpp.md) | Protocol unit tests |
| 11 | [test_integration.sh.md](11-test_integration.sh.md) | End-to-end test in bash |
| 12 | [Makefile.md](12-Makefile.md) | How everything is compiled |
| 13 | [interview-prep.md](13-interview-prep.md) | Full system design, trade-offs, and likely interview questions with answers |

If you only have one hour before an interview, read **01**, **06** and **13**.

## How to read each file

- Code is shown in small chunks with its line numbers, followed by a plain
  explanation.
- **C++ note** boxes explain language features you may not have used in DSA
  (pointers to pointers, casts, `std::optional`, RAII, and so on).
- **CN refresher** boxes explain the networking idea behind a line of code,
  with examples. They repeat a little between files on purpose, so each file
  can be read on its own.

## The project in one picture

```
  build/client set foo bar                         build/server
 ┌──────────────────────────┐                ┌──────────────────────────────────┐
 │ client.cpp               │                │ server.cpp                       │
 │  argv -> encodeRequest   │   TCP over     │  poll() event loop               │
 │  writeFrame ───────────────► 127.0.0.1 ──────►  handleRead -> handleRequests  │
 │                          │   port 1234    │     parseRequest -> runCommand   │
 │  readFrame  ◄──────────────────────────────────  KvStore (get/set/del)       │
 │  parseResponse -> print  │                │        └── HMap (hashtable.cpp)  │
 └──────────────────────────┘                │  handleWrite                     │
         uses protocol.cpp                   └──────────────────────────────────┘
                                                      uses protocol.cpp
```
