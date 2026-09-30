# 07 — `src/client.cpp`

**What it is:** a tiny command-line program that sends **one** command to the
server and prints the reply, then exits.

```sh
build/client set foo bar   # OK
build/client get foo       # bar
build/client get nope      # (nil)
build/client ping          # (error) unknown command or wrong number of arguments
```

Unlike the server, the client talks to exactly one server and has nothing
else to do while waiting, so it uses plain **blocking** I/O: send, then sleep
until the reply arrives.

---

## Lines 1–8: includes

```cpp
#include <cstdio>     // perror
#include <iostream>   // std::cout, std::cerr
#include <string>
#include <vector>

#include <unistd.h>   // close

#include "protocol.h"
```

All socket work is hidden inside `protocol.cpp` helpers, so this file only
needs `close` from the OS API.

---

## Lines 10–14: check arguments

```cpp
int main(int argc, char **argv) {
    if (argc < 2) {
        std::cerr << "usage: " << argv[0] << " <cmd> [args...]\n";
        return 1;
    }
```

> **C++ note — `argc` / `argv`:** how a program receives its command-line
> arguments. For `build/client set foo bar`:
>
> | | value |
> |---|---|
> | `argc` | 4 |
> | `argv[0]` | `"build/client"` (the program's own name) |
> | `argv[1]` | `"set"` |
> | `argv[2]` | `"foo"` |
> | `argv[3]` | `"bar"` |
>
> `argc < 2` means no command was given.

> **C++ note — `std::cerr` vs `std::cout`:** `cout` is standard output
> (results); `cerr` is standard error (messages about problems). Keeping them
> separate lets scripts capture results without error text mixed in.
> Returning `1` from `main` is the exit status; non-zero means failure.

---

## Lines 16–20: encode the request

```cpp
    Buffer request;
    if (!encodeRequest(request, std::vector<std::string>(argv + 1, argv + argc))) {
        std::cerr << "request too large\n";
        return 1;
    }
```

Turn every argument after the program name into a `std::string`, and encode
the list into the request format:

```
set foo bar  ->  03000000 03000000 736574 03000000 666f6f 03000000 626172  (25 bytes)
```

If the result is bigger than `kMaxMsg` (4096), refuse to send it (the server
would reject it and close the connection anyway).

> **C++ note — `std::vector<std::string>(argv + 1, argv + argc)`:** the
> vector's "range constructor": build a vector from every element between
> two pointers. `argv + 1` skips the program name. Each `char*` is converted
> to a `std::string`. It's a temporary, passed straight into the function.

---

## Lines 22–26: connect

```cpp
    int fd = connectToServer();
    if (fd < 0) {
        perror("connect()");
        return 1;
    }
```

Open a TCP connection to `127.0.0.1:1234` (see [03](03-protocol.cpp.md#lines-144161-connecttoserver)).
If the server isn't running, this prints `connect(): Connection refused`.

> **CN refresher — "Connection refused":** when a TCP connection request
> (SYN) arrives at a port with nobody listening, the other machine's kernel
> immediately answers with a **RST** (reset). `connect()` then fails with
> `ECONNREFUSED`. If instead the machine didn't answer at all (e.g. a
> firewall dropped the packet), `connect()` would wait and eventually fail
> with a timeout.

> **CN refresher — what happens during `connect()`:** the kernel picks a
> free ephemeral port for us (say 52311) and performs the TCP 3-way
> handshake: SYN → SYN-ACK → ACK. When `connect()` returns, the connection
> `127.0.0.1:52311 ↔ 127.0.0.1:1234` is open.

---

## Lines 27–36: send the request, read the reply

```cpp
    if (!writeFrame(fd, request)) {
        std::cerr << "failed to send request\n";
        return 1;
    }
    auto payload = readFrame(fd);
    close(fd);
    if (!payload) {
        std::cerr << "failed to read response\n";
        return 1;
    }
```

1. `writeFrame` prepends the 4-byte length and writes the whole frame
   (29 bytes for `set foo bar`).
2. `readFrame` blocks until the server's full reply frame has arrived and
   returns its payload.
3. Close the socket: we're done with the connection either way.
4. If reading failed (the server closed the connection or sent something
   invalid), report it.

> **CN refresher — who closes first, and TIME_WAIT:** the client calls
> `close()` first. That sends a TCP FIN; the server's next `read()` returns
> 0 and it closes its side. Because the client closed first, the **client's**
> port sits in the TIME_WAIT state for ~30 seconds afterwards. That's
> harmless for one command. The integration test runs 10,000 clients in a
> row, leaving up to 10,000 ports in TIME_WAIT, still under macOS's ~16,000
> ephemeral ports. See [01 §5](01-networking-refresher.md#closing-fin-and-time_wait).

> **C++ note — `auto payload`:** the type is
> `std::optional<std::vector<uint8_t>>`. `auto` saves typing it out.

---

## Lines 38–42: decode the reply

```cpp
    auto response = parseResponse(payload->data(), payload->size());
    if (!response) {
        std::cerr << "bad response\n";
        return 1;
    }
```

Turn the payload bytes into a `Response` (status + data). `payload->data()`
calls `.data()` on the vector inside the optional.

---

## Lines 44–56: print

```cpp
    switch (response->status) {
    case ResponseStatus::Ok:
        std::cout << (response->data.empty() ? "OK" : response->data) << "\n";
        break;
    case ResponseStatus::Nx:
        std::cout << "(nil)\n";
        break;
    case ResponseStatus::Err:
        std::cout << "(error) unknown command or wrong number of arguments\n";
        break;
    }
    return 0;
}
```

| Status | Printed |
|---|---|
| `Ok` with data | the value, e.g. `bar` |
| `Ok` without data | `OK` |
| `Nx` | `(nil)` (same wording as `redis-cli`) |
| `Err` | the error message |

This is where the empty-value flaw shows up: after `set k ""`, `get k`
returns `Ok` with no data, so the client prints `OK` instead of an empty line.

> **C++ note — the `?:` expression:** `"OK"` is a C string literal and
> `response->data` is a `std::string`. The two branches of `?:` must have a
> common type, so the literal is converted to `std::string`. The result is
> then printed.

> **C++ note — `switch` on an `enum class`:** with `-Wall`, the compiler
> warns if a `case` is missing for any enum value, which is a nice safety net.
