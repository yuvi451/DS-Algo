# 02 — `src/protocol.h`

**What it is:** the shared "contract" between the client, the server and the
benchmark. It declares the message format, a byte-buffer class, and helper
functions. Every other `.cpp` file includes it.

**Why a header:** in C++, a `.h` file *declares* things (says they exist and
what their types are); the matching `.cpp` file *defines* them (the actual
code). Other files include the header so the compiler knows how to call
the functions, and the linker later connects the calls to the code in
`protocol.cpp`.

---

## Lines 1–2, 65: include guard

```cpp
#ifndef PROTOCOL_H
#define PROTOCOL_H
...
#endif
```

If a header gets included twice in the same `.cpp` (directly or through
another header), everything would be declared twice and the compiler would
complain. This guard says: "if `PROTOCOL_H` isn't defined yet, define it and
include the contents; otherwise skip everything."

> **C++ note:** `#pragma once` does the same thing in one line and is supported
> by every major compiler. Include guards are the older, fully standard way.

---

## Lines 4–9: standard includes

```cpp
#include <cstddef>      // size_t
#include <cstdint>      // uint8_t, uint16_t, uint32_t, uint64_t
#include <optional>     // std::optional
#include <string>       // std::string
#include <string_view>  // std::string_view
#include <vector>       // std::vector
```

> **C++ note — fixed-width integers:** in DSA you mostly used `int` and
> `long long`, whose sizes can differ between machines. For network
> protocols we need *exact* sizes, because the other side must read the same
> number of bytes. `uint32_t` is always exactly 4 bytes, unsigned; `uint8_t`
> is exactly 1 byte (a raw byte). `size_t` is the unsigned type used for
> sizes and indexes (8 bytes on a 64-bit machine).

---

## Lines 11–15: constants

```cpp
// All integers on the wire are 32-bit in host byte order (little-endian on
// x86/ARM). See README.md for the full message layout.
constexpr size_t kMaxMsg = 4096;
constexpr size_t kHeaderLen = 4;
constexpr uint16_t kServerPort = 1234;
```

- **`kMaxMsg = 4096`**: the largest payload allowed in one frame. This
  protects the server: without a limit, a client could claim "my message is
  4 GB" and make the server allocate that much.
- **`kHeaderLen = 4`**: every frame starts with a 4-byte length.
- **`kServerPort = 1234`**: the TCP port the server listens on and the client
  connects to. `uint16_t` because port numbers are 16-bit.

> **C++ note — `constexpr`:** a constant known at compile time. Better than
> `#define` because it has a type and obeys scope rules. The `k` prefix is a
> common naming style for constants (Google's C++ style).

> **CN refresher — "on the wire" and byte order:** "on the wire" means "as
> bytes sent over the network". A 4-byte number can be stored
> least-significant byte first (**little-endian**) or most-significant byte
> first (**big-endian**, also called **network byte order**). The number 25
> is `19 00 00 00` in little-endian and `00 00 00 19` in big-endian. This
> project writes its own lengths in **host order**, i.e. whatever the CPU
> uses. On Intel and Apple Silicon that's little-endian. Standard internet
> protocols use big-endian, so this is a known simplification. See
> [01 §11](01-networking-refresher.md#11-byte-order-endianness).

---

## Lines 17–21: response status

```cpp
enum class ResponseStatus : uint8_t {
    Ok = 0,
    Err = 1,
    Nx = 2,
};
```

Every reply starts with one status byte:

| Status | Byte | Meaning |
|---|---|---|
| `Ok` | 0 | Success. For `get`, the value follows. |
| `Err` | 1 | Unknown command or wrong number of arguments |
| `Nx` | 2 | "Non-existent": the key wasn't found |

> **C++ note — `enum class` vs `enum`:**
> - Values must be written with the prefix: `ResponseStatus::Ok`, not `Ok`.
>   So `Ok` can't clash with some other `Ok`.
> - It doesn't silently convert to `int`. You must write
>   `static_cast<uint8_t>(status)`, which makes byte-level code explicit.
> - `: uint8_t` sets the underlying type, so the enum is exactly 1 byte,
>   matching the 1 status byte on the wire.

---

## Lines 23–34: `Buffer`

```cpp
class Buffer {
public:
    void append(const uint8_t *data, size_t len);
    void append(std::string_view s);
    void consume(size_t n);  // drop n bytes from the front

    const uint8_t *data() const { return buf_.data(); }
    size_t size() const { return buf_.size(); }

private:
    std::vector<uint8_t> buf_;
};
```

A growable array of raw bytes, used for everything that goes over the
network: requests being built, a connection's unread input, a connection's
unsent output.

- **`append(data, len)`**: add raw bytes at the end.
- **`append(string_view)`**: add a string's bytes at the end. Two functions
  with the same name but different parameters is **overloading**.
- **`consume(n)`**: remove `n` bytes from the front, once they've been
  processed (input) or sent (output).
- **`data()`**: pointer to the first byte, for passing to `read`/`write`/`memcpy`.
- **`size()`**: number of bytes currently stored.

Why wrap `std::vector` at all? It names the operations the code actually
needs (append at back, remove from front) and hides everything else.

> **C++ note — `const` at the end of a method:** `size_t size() const`
> promises the method doesn't change the object. You can call it on a
> `const Buffer&`. Methods defined inside the class body (like `data()`) are
> automatically `inline`, which is fine for one-liners.

> **C++ note — `std::string_view`:** a lightweight "view" of characters owned
> by someone else: just a pointer and a length, no copy. You can pass a
> `std::string`, a string literal like `"hello"`, or part of a string. Use
> it for read-only string parameters. Never store it longer than the string
> it points into.

> **C++ note — trailing underscore:** `buf_` marks a private member
> variable, so you can tell it apart from locals at a glance.

---

## Lines 36–38: requests

```cpp
// Request payload: [nargs] then [len][bytes] per arg.
bool encodeRequest(Buffer &out, const std::vector<std::string> &args);  // false if > kMaxMsg
std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len);
```

A request is a list of strings, like a command line (`set foo bar` →
`{"set", "foo", "bar"}`). Its byte layout:

```
[nargs: 4 bytes] [len1: 4 bytes][arg1 bytes] [len2: 4 bytes][arg2 bytes] ...
```

**Worked example: `set foo bar`** (hex, little-endian):

```
03 00 00 00                 nargs = 3
03 00 00 00  73 65 74       len 3, "set"
03 00 00 00  66 6f 6f       len 3, "foo"
03 00 00 00  62 61 72       len 3, "bar"
                            total payload = 4 + 3 × (4 + 3) = 25 bytes
```

- `encodeRequest` appends these bytes to `out`, and returns `false` if the
  result is too big to send.
- `parseRequest` does the reverse. It returns the strings, or "nothing" if
  the bytes are malformed.

Why length-prefix each string instead of separating them with spaces? So
that keys and values can contain **any** bytes, including spaces, newlines
or zero bytes. This is called being **binary-safe**.

> **C++ note — `std::optional<T>`:** either holds a `T` or holds nothing
> (`std::nullopt`). It replaces "return -1 / nullptr on failure". Usage:
> ```cpp
> auto args = parseRequest(p, n);
> if (!args) { /* failed */ }
> args->size();   // access members with ->
> (*args)[0];     // or dereference with *
> ```

> **C++ note — why `const std::vector<std::string> &args`:** passing by
> `const &` avoids copying the whole vector and promises not to modify it.
> Same idea as passing `const vector<int>&` in DSA.

---

## Lines 40–48: responses

```cpp
// Response payload: [1-byte status] then, only if data is non-empty, [len][bytes].
// So an empty-string value looks the same on the wire as "no value".
void encodeResponse(Buffer &out, ResponseStatus status, std::string_view data = {});

struct Response {
    ResponseStatus status;
    std::string data;
};
std::optional<Response> parseResponse(const uint8_t *data, size_t len);
```

Response layout:

```
[status: 1 byte]                          when there's no data (set, del, NX, ERR)
[status: 1 byte][len: 4 bytes][bytes]     when there is data (get that found a value)
```

**Examples:**

```
set foo bar  ->  00                        (Ok, no data)          1 byte
get foo      ->  00  03 00 00 00  62 61 72 (Ok, "bar")            8 bytes
get nope     ->  02                        (Nx)                   1 byte
```

The comment on line 41 flags a real design flaw: because an empty string
isn't encoded, `get` of a key whose value is `""` looks exactly like `set`'s
plain `Ok`. The client can't tell them apart.

`Response` is just a small struct bundling what `parseResponse` found.

> **C++ note — default argument `= {}`:** `std::string_view data = {}` means
> callers can leave it out: `encodeResponse(out, ResponseStatus::Nx)` passes
> an empty view. Default arguments go only in the declaration (the header),
> not repeated in the `.cpp`.

---

## Lines 50–58: framing

```cpp
// Frame: [payload length][payload].
void appendFrame(Buffer &out, const Buffer &payload);

enum class FrameStatus {
    Incomplete,  // wait for more bytes
    Malformed,   // declared length exceeds kMaxMsg
    Complete,
};
FrameStatus tryParseFrame(const uint8_t *buf, size_t len, size_t &payloadLen);
```

Every request and response payload is wrapped in a **frame**: a 4-byte
length followed by the payload. So the full bytes sent for `set foo bar` are
`19 00 00 00` (25) followed by the 25 payload bytes: 29 bytes total.

- **`appendFrame`**: write `[length][payload]` onto `out`.
- **`tryParseFrame`**: look at the bytes received so far and say which of
  three situations we're in. On `Complete`, it also writes the payload
  length into `payloadLen`.

Why three outcomes instead of `std::optional`? Because the server reacts
differently to each: `Incomplete` → keep the connection and wait for more
bytes; `Malformed` → close the connection; `Complete` → process it. An
`optional` can only say "value or nothing", which would merge the first two.

> **C++ note — output parameter `size_t &payloadLen`:** passing by
> non-const reference lets the function write a second result back to the
> caller. An alternative would be returning a struct.

> **CN refresher — why framing is needed:** TCP delivers a stream of bytes
> with **no message boundaries**. If a client sends two 29-byte requests,
> the server might receive 58 bytes in one `read()`, or 10 then 48. The
> length prefix is how the receiver finds where each message ends. See
> [01 §6](01-networking-refresher.md#6-tcp-is-a-byte-stream-why-framing-exists).

---

## Lines 60–63: blocking helpers

```cpp
// Blocking helpers used by the client and the load tester.
int connectToServer();  // -1 on failure, errno set
bool writeFrame(int fd, const Buffer &payload);
std::optional<std::vector<uint8_t>> readFrame(int fd);  // returns the payload only
```

These are used by programs that talk to **one** server and are happy to wait
(the client and benchmark). The server does **not** use them, because the
server must never wait on one client.

- **`connectToServer`**: open a TCP connection to `127.0.0.1:1234`. Returns
  the socket's fd, or -1.
- **`writeFrame`**: send one framed message, waiting until every byte is written.
- **`readFrame`**: wait until one complete frame arrives, and return its payload.

> **CN refresher — blocking I/O:** a blocking `read()` puts the calling
> thread to sleep until data arrives. That's exactly what a client wants
> ("send my command, wait for the answer"). A server with 200 clients can't
> do this, because while it sleeps waiting on one client it can't serve the
> other 199. See [01 §9](01-networking-refresher.md#9-blocking-vs-non-blocking-sockets).

> **CN refresher — what an `int fd` is:** a file descriptor, the small
> integer the OS gives you to refer to an open socket. All socket functions
> (`read`, `write`, `close`) take it. See
> [01 §7](01-networking-refresher.md#7-sockets-and-file-descriptors).
