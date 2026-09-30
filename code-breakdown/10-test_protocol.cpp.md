# 10 — `test/test_protocol.cpp`

**What it is:** unit tests for `protocol.cpp`: the `Buffer` class,
request/response encoding, framing, and frame I/O over a real socket. Built
with AddressSanitizer (`make test-protocol`), so out-of-bounds reads in the
parsers would be caught.

---

## Lines 1–8: includes

```cpp
#include <cassert>
#include <cstdio>
#include <cstring>        // std::memcmp, std::memcpy

#include <sys/socket.h>   // socketpair
#include <unistd.h>       // close

#include "../src/protocol.h"
```

---

## `testBufferAppendGrows` (line 10)

Append 1,000 bytes one at a time (values 0, 1, …, 255, 0, 1, …) and check
they're all there, in order. Makes sure the buffer grows correctly past its
initial capacity.

`static_cast<uint8_t>(i)` wraps `i` into 0–255, which is why the values repeat.

---

## `testBufferConsume` (line 23)

```cpp
    buf.append("hello world");
    buf.consume(6);
    assert(buf.size() == 5);
    assert(std::memcmp(buf.data(), "world", 5) == 0);
```

Remove `"hello "` from the front; `"world"` must remain.

> **C++ note — `memcmp(a, b, n)`:** compares `n` bytes; returns 0 if equal.
> Used instead of string comparison because a `Buffer` is raw bytes, not a
> null-terminated string.

---

## `testRequestRoundtrip` (line 32)

```cpp
    assert(encodeRequest(out, {"set", "foo", "bar"}));
    auto parsed = parseRequest(out.data(), out.size());
    assert((*parsed == std::vector<std::string>{"set", "foo", "bar"}));
```

**Round-trip test:** encode, then decode, and expect the original back. The
simplest way to test an encoder/decoder pair.

> **C++ note — the double parentheses in `assert((...))`:** `assert` is a
> macro, and macros split their argument on commas. The braces list
> `{"set", "foo", "bar"}` contains commas, so without the extra parentheses
> the preprocessor would think `assert` got three arguments.

---

## `testRequestRejectsTruncated` (line 42)

```cpp
    uint32_t nargs = 5;  // claims 5 args, provides none
    std::memcpy(bad, &nargs, 4);
    assert(!parseRequest(bad, 4).has_value());
```

A malicious or broken message that claims 5 arguments but contains none.
The parser must say "invalid", not read past the end of the 4 bytes. Under
ASan, an out-of-bounds read here would crash the test.

---

## `testResponseRoundtripWithData` (line 50) and `testResponseRoundtripStatusOnly` (line 61)

Round-trip an `Ok` + `"bar"` response and a data-less `Nx` response, checking
status and data survive.

---

## `testTryParseFrame` (line 72)

```cpp
    size_t payloadLen = 0;
    assert(tryParseFrame(framed.data(), kHeaderLen, payloadLen) == FrameStatus::Incomplete);
    assert(tryParseFrame(framed.data(), framed.size() - 1, payloadLen) == FrameStatus::Incomplete);
    assert(tryParseFrame(framed.data(), framed.size(), payloadLen) == FrameStatus::Complete);
    assert(payloadLen == payload.size());
    assert(kHeaderLen + payloadLen == framed.size());
```

Build a real frame, then pretend only part of it has arrived:
1. Only the 4-byte header → `Incomplete`.
2. Everything except the last byte → `Incomplete`.
3. The whole frame → `Complete`, with the right payload length.

> **CN refresher — why this test matters:** on a real TCP connection, the
> server sees exactly these situations. TCP can deliver a message in pieces,
> so the server calls `tryParseFrame` after every `read()` with whatever it
> has so far. Getting "incomplete" wrong would make the server either
> process half a request or wait forever.

---

## `testTryParseFrameRejectsOversized` (line 87)

A header claiming `kMaxMsg + 1` bytes must be `Malformed` immediately, from
just the 4 header bytes, without waiting for a payload that will never be
accepted.

---

## `testFrameIoOverSocketpair` (line 96)

```cpp
    int fds[2];
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, fds) == 0);

    Buffer payload;
    payload.append("ping");
    assert(writeFrame(fds[0], payload));

    auto got = readFrame(fds[1]);
    assert(got.has_value());
    assert(got->size() == 4);
    assert(std::memcmp(got->data(), "ping", 4) == 0);
```

Tests the real blocking I/O functions (`writeFrame`, `readFrame`, and inside
them `writeAll`, `readFull`) with real file descriptors, but without needing
a server.

> **CN refresher — `socketpair`:** creates **two sockets already connected
> to each other**, inside one process. Whatever you write to `fds[0]` can be
> read from `fds[1]`, and vice versa.
>
> - `AF_UNIX` means a **Unix domain socket**: communication between
>   processes on the same machine through the kernel, with no IP addresses,
>   ports or TCP involved.
> - `SOCK_STREAM` means it behaves like a byte stream, same as TCP from our
>   code's point of view. So `read`/`write` behave the same way as on the
>   server's sockets.
>
> This lets the test exercise socket I/O without opening a port. Real
> databases use Unix sockets too: PostgreSQL and Redis can both listen on a
> socket *file* (like `/tmp/redis.sock`) for faster local connections.

The write fits comfortably in the socket's buffer, so `writeFrame` returns
before anything reads it, and the test doesn't need a second thread.

```cpp
    close(fds[0]);
    close(fds[1]);
```

Close both ends so the test doesn't leak file descriptors.

---

## `main` (line 114)

Run all nine tests in order.
