# 03 — `src/protocol.cpp`

**What it is:** the code behind everything declared in `protocol.h`: turning
commands into bytes and back, framing, and blocking socket helpers for the
client and benchmark.

**Used by:** `server.cpp`, `client.cpp`, `bench/loadtest.cpp`, and the
protocol unit test.

---

## Lines 1–10: includes

```cpp
#include "protocol.h"

#include <cassert>   // assert
#include <cstring>   // std::memcpy

#include <arpa/inet.h>    // htons, htonl
#include <netinet/in.h>   // sockaddr_in, INADDR_LOOPBACK, IPPROTO_TCP
#include <netinet/tcp.h>  // TCP_NODELAY
#include <sys/socket.h>   // socket, connect, setsockopt
#include <unistd.h>       // read, write, close
```

The first group is the C++ standard library. The second group is **POSIX**:
the operating-system API shared by macOS and Linux. C++ has no standard
networking library, so every C++ network program uses these C functions
directly.

> **C++ note — `"..."` vs `<...>`:** quotes mean "look in this project
> first" (our own headers); angle brackets mean "look in the system include
> paths".

---

## Lines 12, 48: anonymous namespace

```cpp
namespace {
...
}  // namespace
```

Everything inside `namespace { }` is **private to this file**. Other `.cpp`
files can't see or call `appendU32`, `readU32`, `readFull` or `writeAll`.
That keeps the public API (the header) small and avoids name clashes when
all the files are linked together.

> **C++ note:** this is the modern replacement for marking functions
> `static` at file level (you'll still see `static` used that way in
> `server.cpp`; both mean the same here).

---

## Lines 14–16: `appendU32`

```cpp
void appendU32(Buffer &out, uint32_t v) {
    out.append(reinterpret_cast<const uint8_t *>(&v), 4);
}
```

Appends the 4 raw bytes of the number `v` to the buffer. `&v` is the address
of `v` in memory; we reinterpret that as "pointer to bytes" and copy 4 of
them.

On a little-endian Mac, `appendU32(out, 25)` appends `19 00 00 00`.

> **C++ note — `reinterpret_cast`:** "treat this pointer as a pointer to a
> different type, don't change the bits". It's the most dangerous cast and
> only safe in specific cases. Viewing any object as bytes (`uint8_t*`,
> `char*`, `unsigned char*`) is one of the allowed, well-defined cases.

> **C++ casts cheat sheet** (you'll see all of these in the project):
>
> | Cast | Use |
> |---|---|
> | `static_cast<T>(x)` | Normal, checked conversions: `size_t`↔`long`, enum↔int, base class pointer → derived class pointer |
> | `reinterpret_cast<T*>(p)` | View memory as a different type (bytes ↔ objects, `sockaddr_in*` → `sockaddr*`) |
> | `const_cast<T*>(p)` | Add or remove `const` |
> | `(T)x` C-style | Does any of the above silently. Avoided in modern C++. |

---

## Lines 18–22: `readU32`

```cpp
uint32_t readU32(const uint8_t *data) {
    uint32_t v;
    std::memcpy(&v, data, 4);
    return v;
}
```

The reverse: read 4 bytes starting at `data` and return them as a number.

Why `memcpy` instead of `*(uint32_t *)data`? Two reasons:
1. **Alignment:** some CPUs require a 4-byte number to start at an address
   divisible by 4. Our length fields can be at any offset (e.g. byte 1 of a
   response), so a direct read could crash or be slow.
2. **Strict aliasing:** C++ only guarantees correct behaviour when you read
   memory through its real type. Reading bytes *as* a `uint32_t` breaks
   that rule; `memcpy` doesn't. Compilers turn this `memcpy` into a single
   load instruction, so it costs nothing.

---

## Lines 24–34: `readFull`

```cpp
bool readFull(int fd, uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = read(fd, buf, n);
        if (rv <= 0) {
            return false;
        }
        n -= static_cast<size_t>(rv);
        buf += rv;
    }
    return true;
}
```

Read **exactly** `n` bytes, however many `read()` calls it takes.

- `read(fd, buf, n)` asks for up to `n` bytes. It returns how many it
  actually got (`rv`), `0` if the other side closed the connection, or `-1`
  on error.
- If `rv <= 0`, give up (connection closed or broken).
- Otherwise subtract what we got from `n`, move `buf` forward by `rv` bytes
  (pointer arithmetic), and loop for the rest.

> **CN refresher — partial reads:** `read(fd, buf, 100)` does **not** wait
> for 100 bytes. On a blocking socket it waits until **at least one** byte
> is available, then returns whatever is in the kernel's receive buffer.
> **Example:** the server sends a 12-byte reply, but TCP delivers it as 5
> bytes then 7 bytes. The first `read` returns 5; the loop calls `read`
> again for the remaining 7. See
> [01 §8](01-networking-refresher.md#8-kernel-buffers-what-read-and-write-really-do).

> **C++ note — `ssize_t`:** a *signed* size type, so `read` can return `-1`.
> We then `static_cast<size_t>` it before subtracting from the unsigned `n`,
> to avoid signed/unsigned mix-ups.

---

## Lines 36–46: `writeAll`

```cpp
bool writeAll(int fd, const uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = write(fd, buf, n);
        if (rv <= 0) {
            return false;
        }
        n -= static_cast<size_t>(rv);
        buf += rv;
    }
    return true;
}
```

Same idea for writing: keep calling `write()` until all `n` bytes are
written.

> **CN refresher — partial writes:** `write()` copies your bytes into the
> kernel's **send buffer** and returns; the kernel sends them over the
> network later. If the send buffer only has room for part of your data,
> `write()` copies that part and returns the smaller count. Our messages are
> tiny (at most 4100 bytes), so in practice one `write` is enough, but
> correct code must still handle the partial case.

---

## Lines 50–52: `Buffer::append(data, len)`

```cpp
void Buffer::append(const uint8_t *data, size_t len) {
    buf_.insert(buf_.end(), data, data + len);
}
```

Insert the byte range `[data, data + len)` at the end of the vector. Raw
pointers work as iterators here, the same way `v.insert(v.end(), a, a + n)`
works with an array in DSA. The vector grows automatically (amortised O(1)
per byte).

> **C++ note — `Buffer::`:** the method was declared inside `class Buffer`
> in the header; `Buffer::append` defines it outside the class.

---

## Lines 54–56: `Buffer::append(string_view)`

```cpp
void Buffer::append(std::string_view s) {
    append(reinterpret_cast<const uint8_t *>(s.data()), s.size());
}
```

A convenience overload: view the string's `char`s as bytes and reuse the
first `append`.

---

## Lines 58–61: `Buffer::consume`

```cpp
void Buffer::consume(size_t n) {
    assert(n <= buf_.size());
    buf_.erase(buf_.begin(), buf_.begin() + static_cast<long>(n));
}
```

Remove the first `n` bytes.

- `assert(...)` crashes the program with a message if the condition is
  false. It catches bugs during development ("we never consume more than we
  have").
- `erase` on the front of a vector shifts every remaining byte left, so it
  costs O(remaining bytes). With many pipelined requests in one buffer this
  adds up to O(n²). A faster design keeps a "start offset" and only
  compacts occasionally, or uses a ring buffer. Listed as a known limitation.

> **C++ note — `static_cast<long>(n)`:** iterator arithmetic uses a signed
> type, while `n` is unsigned `size_t`. The cast makes that conversion
> explicit and silences a compiler warning.

> **C++ note — `assert` and `NDEBUG`:** asserts are removed if you compile
> with `-DNDEBUG`. This project never does, so they're always active.

---

## Lines 63–70: `encodeRequest`

```cpp
bool encodeRequest(Buffer &out, const std::vector<std::string> &args) {
    appendU32(out, static_cast<uint32_t>(args.size()));
    for (const auto &arg : args) {
        appendU32(out, static_cast<uint32_t>(arg.size()));
        out.append(arg);
    }
    return out.size() <= kMaxMsg;
}
```

1. Write the number of arguments.
2. For each argument, write its length then its bytes.
3. Return whether the result fits in one frame.

Trace for `{"get", "k"}`:

```
02 00 00 00        nargs = 2
03 00 00 00 67 65 74    "get"
01 00 00 00 6b          "k"
```

> **C++ note — `for (const auto &arg : args)`:** range-based for loop.
> `auto` lets the compiler figure out the type (`std::string`), and `const &`
> avoids copying each string.

> **C++ note — `out.append(arg)`:** `arg` is a `std::string`, which converts
> automatically to `std::string_view`, so the second `append` overload is
> chosen.

---

## Lines 72–100: `parseRequest`

```cpp
std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len) {
    if (len < 4) {
        return std::nullopt;
    }
    uint32_t nargs = readU32(data);
    if (nargs > 1024) {
        return std::nullopt;
    }
```

This function reads **untrusted input** (bytes from any client), so it
checks every length before using it.

- **Line 73:** fewer than 4 bytes means there's not even an `nargs` field.
- **Line 77:** cap the argument count at 1024, so a client can't make us
  `reserve` space for 4 billion strings.
- `std::nullopt` means "failed".

```cpp
    size_t pos = 4;
    std::vector<std::string> args;
    args.reserve(nargs);
```

`pos` is our read position in the payload, starting right after `nargs`.
`reserve` pre-allocates space for `nargs` strings so the vector doesn't
reallocate while we add them.

```cpp
    for (uint32_t i = 0; i < nargs; i++) {
        if (pos + 4 > len) {
            return std::nullopt;
        }
        uint32_t l = readU32(data + pos);
        pos += 4;
        if (pos + l > len) {
            return std::nullopt;
        }
        args.emplace_back(reinterpret_cast<const char *>(data + pos), l);
        pos += l;
    }
```

For each argument:
1. Check there are 4 bytes left for its length (line 85).
2. Read the length `l`, advance `pos`.
3. Check the string's bytes are really there (line 90). Without this check,
   a client could claim a 1000-byte string in a 10-byte message and we'd
   read past the end of the buffer (a classic security bug).
4. Build a `std::string` from `l` bytes at `data + pos`, advance `pos`.

> **C++ note — `emplace_back(ptr, len)`:** constructs the string directly
> inside the vector, using the `std::string(const char*, size_t)`
> constructor. Same result as `push_back(std::string(ptr, len))`, without a
> temporary.

```cpp
    if (pos != len) {
        return std::nullopt;
    }
    return args;
}
```

After all arguments, we must be exactly at the end. Extra trailing bytes
mean the message is malformed.

> **C++ note — `return args;`** converts the vector into an
> `std::optional<std::vector<std::string>>` holding it. The vector is moved,
> not copied.

---

## Lines 102–109: `encodeResponse`

```cpp
void encodeResponse(Buffer &out, ResponseStatus status, std::string_view data) {
    uint8_t s = static_cast<uint8_t>(status);
    out.append(&s, 1);
    if (!data.empty()) {
        appendU32(out, static_cast<uint32_t>(data.size()));
        out.append(data);
    }
}
```

Write the status byte, then the data (length + bytes) only if there is any.
This `if` is exactly why an empty value and "no value" look the same.

---

## Lines 111–123: `parseResponse`

```cpp
std::optional<Response> parseResponse(const uint8_t *data, size_t len) {
    if (len < 1) {
        return std::nullopt;
    }
    auto status = static_cast<ResponseStatus>(data[0]);
    if (len == 1) {
        return Response{status, std::string()};
    }
    if (len < 5 || 5 + static_cast<size_t>(readU32(data + 1)) != len) {
        return std::nullopt;
    }
    return Response{status, std::string(reinterpret_cast<const char *>(data + 5), len - 5)};
}
```

- Empty payload: invalid.
- Byte 0 is the status.
- Exactly 1 byte: status only, no data.
- Otherwise we need at least 5 bytes (status + 4-byte length), and
  `1 + 4 + length` must equal the total. `||` short-circuits, so `readU32`
  is only called when there are at least 5 bytes.
- The data is the bytes after position 5.

> **C++ note — `Response{status, ...}`:** aggregate initialization: fills the
> struct's fields in declaration order, no constructor needed.

Note: the status byte isn't validated. A byte like `7` would become a
`ResponseStatus` with no matching name. Only our own server sends responses,
so this doesn't happen in practice.

---

## Lines 125–128: `appendFrame`

```cpp
void appendFrame(Buffer &out, const Buffer &payload) {
    appendU32(out, static_cast<uint32_t>(payload.size()));
    out.append(payload.data(), payload.size());
}
```

Frame = 4-byte length + payload. Used by both the server (for replies) and
`writeFrame` (for requests).

---

## Lines 130–142: `tryParseFrame`

```cpp
FrameStatus tryParseFrame(const uint8_t *buf, size_t len, size_t &payloadLen) {
    if (len < kHeaderLen) {
        return FrameStatus::Incomplete;
    }
    payloadLen = readU32(buf);
    if (payloadLen > kMaxMsg) {
        return FrameStatus::Malformed;
    }
    if (len < kHeaderLen + payloadLen) {
        return FrameStatus::Incomplete;
    }
    return FrameStatus::Complete;
}
```

Given what the server has received so far (`buf`, `len` bytes), decide:

| Situation | Result |
|---|---|
| Not even 4 bytes yet | `Incomplete` — wait |
| Header says > 4096 | `Malformed` — close the connection |
| Header OK but payload hasn't fully arrived | `Incomplete` — wait |
| Header and full payload are here | `Complete` |

**Example** (a 29-byte `set foo bar` frame arriving in pieces):

```
received 3 bytes   -> Incomplete (no full header)
received 20 bytes  -> header says 25, need 29 total -> Incomplete
received 29 bytes  -> Complete, payloadLen = 25
received 40 bytes  -> Complete, payloadLen = 25 (the other 11 bytes are the next request)
```

The size check happens **before** waiting for the payload, so a bad client
is rejected as soon as its 4-byte header arrives.

> **CN refresher:** this function exists *because* TCP is a stream. The
> server's `read()` returns whatever bytes have arrived, which may be half a
> message or three and a half messages. See
> [01 §6](01-networking-refresher.md#6-tcp-is-a-byte-stream-why-framing-exists).

---

## Lines 144–161: `connectToServer`

```cpp
int connectToServer() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        return -1;
    }
```

`socket()` creates a new socket and returns its fd.
- `AF_INET` = IPv4 addresses.
- `SOCK_STREAM` = a reliable byte stream = **TCP**.
- `0` = pick the default protocol for this type (TCP).

```cpp
    int one = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
```

Turn on `TCP_NODELAY` (turn *off* Nagle's algorithm) for this socket.
`setsockopt` takes a pointer to the option's value and its size, which is
why we need a variable `one` instead of just `1`.

> **CN refresher — Nagle and TCP_NODELAY:** by default, TCP may hold back a
> small write if earlier data hasn't been acknowledged yet, to batch small
> writes into fewer packets (Nagle's algorithm). For a request/response
> client this can add tens of milliseconds of delay. `TCP_NODELAY` says
> "send small writes immediately". Databases and games almost always set it.
> See [01 §12](01-networking-refresher.md#12-nagles-algorithm-and-tcp_nodelay).

```cpp
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(kServerPort);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
```

Fill in the address to connect to: IPv4, port 1234, IP 127.0.0.1.

- `sockaddr_in addr{}` zero-initialises the whole struct (important: it has
  padding fields that must be zero).
- `htons` / `htonl` convert the port and IP into **network byte order**
  (big-endian), which the socket API requires.

> **CN refresher — `htons(1234)`:** 1234 is `0x04D2`. In memory on a Mac
> (little-endian) that's `D2 04`. The network expects `04 D2`. `htons` swaps
> it. Forgetting `htons` is a classic bug: you'd end up connecting to port
> `0xD204` = 53764. See [01 §11](01-networking-refresher.md#11-byte-order-endianness).

> **CN refresher — `INADDR_LOOPBACK`:** the constant for `127.0.0.1`,
> "this machine". Traffic to it never touches a real network card.

```cpp
    if (connect(fd, reinterpret_cast<sockaddr *>(&addr), sizeof(addr)) != 0) {
        close(fd);
        return -1;
    }
    return fd;
}
```

`connect()` performs the TCP 3-way handshake with the server and returns 0
on success. On failure (for example, the server isn't running →
`ECONNREFUSED`), close the socket so we don't leak the fd, and return -1.
`errno` still holds the reason, so the caller can print it with `perror`.

> **C++ note — why `reinterpret_cast<sockaddr *>`:** the socket API was
> designed in C to work with many address types (IPv4 `sockaddr_in`, IPv6
> `sockaddr_in6`, Unix sockets…). They all start with a common header, and
> the functions take a generic `sockaddr*` plus a size. We pass our specific
> struct as the generic type. This is C's version of polymorphism.

> **CN refresher — the client's port:** we never choose one. During
> `connect()`, the kernel assigns a free **ephemeral port** (e.g. 52311), so
> the connection is `127.0.0.1:52311 ↔ 127.0.0.1:1234`.

---

## Lines 163–170: `writeFrame`

```cpp
bool writeFrame(int fd, const Buffer &payload) {
    if (payload.size() > kMaxMsg) {
        return false;
    }
    Buffer frame;
    appendFrame(frame, payload);
    return writeAll(fd, frame.data(), frame.size());
}
```

Refuse oversized payloads (the server would reject them anyway). Build the
header and payload into **one** buffer and send it with one `writeAll`.

Sending in one piece matters:
- Two separate small `write()`s (header, then body) is the classic pattern
  that triggers the Nagle + delayed-ACK delay on sockets without
  `TCP_NODELAY`.
- It's one syscall instead of two, and the server never receives a lone
  4-byte header that forces it to go round the `poll()` loop again before
  the payload arrives.

When this project was cleaned up, merging them into one write raised the
benchmark from ~161K to ~184K ops/sec.

---

## Lines 172–186: `readFrame`

```cpp
std::optional<std::vector<uint8_t>> readFrame(int fd) {
    uint8_t header[kHeaderLen];
    if (!readFull(fd, header, kHeaderLen)) {
        return std::nullopt;
    }
    uint32_t len = readU32(header);
    if (len > kMaxMsg) {
        return std::nullopt;
    }
    std::vector<uint8_t> payload(len);
    if (!readFull(fd, payload.data(), len)) {
        return std::nullopt;
    }
    return payload;
}
```

1. Read exactly 4 header bytes.
2. Decode the length and reject anything too big.
3. Allocate a vector of exactly `len` bytes and read exactly that many into it.
4. Return only the payload (the header has done its job).

If `len` is 0, `readFull` does nothing and returns `true`, giving an empty
payload.

> **C++ note — `uint8_t header[kHeaderLen]`:** a fixed-size array on the
> stack. Allowed because `kHeaderLen` is `constexpr`.
