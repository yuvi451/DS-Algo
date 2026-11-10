---
title: Final code (every file)
module: Reference
time: lookup
---

The complete finished project, pulled straight from the repository each time
the site is built, so it always matches the current implementation. Use it to
compare against your own files.

```text
microredis/
├── Makefile
├── src/
│   ├── protocol.h      constants, encode/parse, framing, blocking I/O           (Part 4)
│   ├── protocol.cpp
│   ├── hashtable.h     Node, Table, HashMap, hashString                          (Part 6)
│   ├── hashtable.cpp
│   ├── server.cpp      runCommand, Conn, poll() event loop                       (Parts 5–6)
│   └── client.cpp      one command per run                                       (Part 5)
├── test/
│   ├── test_protocol.cpp
│   ├── test_hashtable.cpp
│   └── test_integration.sh                                                       (Part 7)
└── bench/
    └── loadtest.cpp                                                              (Part 7)
```

## src/protocol.h

@include ../src/protocol.h

## src/protocol.cpp

@include ../src/protocol.cpp

## src/hashtable.h

@include ../src/hashtable.h

## src/hashtable.cpp

@include ../src/hashtable.cpp

## src/server.cpp

@include ../src/server.cpp

## src/client.cpp

@include ../src/client.cpp

## test/test_protocol.cpp

@include ../test/test_protocol.cpp

## test/test_hashtable.cpp

@include ../test/test_hashtable.cpp

## test/test_integration.sh

@include ../test/test_integration.sh

## bench/loadtest.cpp

@include ../bench/loadtest.cpp

## Makefile

@include ../Makefile
