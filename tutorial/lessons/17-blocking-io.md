---
title: Sending and receiving whole frames
module: The protocol
time: 40 min
---

:::goal
Finish `protocol.cpp` with the **blocking** helpers that the client (and
later the load tester) use: `writeAll`, `readExactly`, `connectToServer`,
`writeFrame` and `readFrame`. Then test real socket I/O without running a
server, using `socketpair()`. After this lesson, `protocol.h` and
`protocol.cpp` are **finished**, identical to the final project.
:::

## Looping until done: `writeAll` and `readExactly`

Remember: `write(fd, data, n)` may accept **fewer** than `n` bytes, and
`read` may return fewer than you asked for. So we loop, keeping track of how
many bytes are `done`:

```cpp
// write() and read() may handle fewer bytes than asked, so loop until done.
bool writeAll(int fd, const string &data) {
    size_t done = 0;
    while (done < data.size()) {
        int n = write(fd, data.data() + done, data.size() - done);
        if (n <= 0) return false;
        done += n;
    }
    return true;
}

bool readExactly(int fd, size_t n, string &out) {
    out.resize(n);
    size_t done = 0;
    while (done < n) {
        int got = read(fd, &out[done], n - done);
        if (got <= 0) return false;  // error, or the other side closed
        done += got;
    }
    return true;
}
```

```text
want 12 bytes:
 read → 5      [■■■■■□□□□□□□]   done = 5
 read → 4      [■■■■■■■■■□□□]   done = 9
 read → 3      [■■■■■■■■■■■■]   done = 12 → finished ✓
```

- `data.data() + done` is the address of the first byte **not yet sent**.
  (Adding a number to an address moves forward that many bytes.)
- `out.resize(n)` makes room for `n` bytes, and `&out[done]` is the address
  where the next bytes should go.

:::why Why is `got <= 0` a failure for `readExactly`?
`-1` is an error. `0` means the other side **closed the connection**. If
that happens before we got all `n` bytes, the message is cut off and we can
never complete it, so we report failure.
:::

## `connectToServer()`

Your Part 3 client code, packaged up, with one addition:

```cpp
int connectToServer() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;
    int yes = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &yes, sizeof(yes));  // send small messages right away

    sockaddr_in addr = {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);  // 127.0.0.1
    if (connect(fd, (sockaddr *)&addr, sizeof(addr)) != 0) {
        close(fd);
        return -1;
    }
    return fd;
}
```

:::net `TCP_NODELAY`: turning off Nagle's algorithm
By default, TCP holds back small writes for a moment hoping to combine them
into one bigger packet (**Nagle's algorithm**). That saves bandwidth for
chatty programs, but for request→response traffic it can add delays of up to
tens of milliseconds. `TCP_NODELAY` says "send small writes immediately".
Almost every database client sets it. (Header `<netinet/tcp.h>`.)
:::

:::why Why `return -1` instead of `die()`?
This is shared code used by several programs. It shouldn't decide to kill
the whole program. It reports failure and lets the caller choose what to
print. Note the `close(fd)` before returning, so we don't leak the socket.
:::

## `writeFrame` and `readFrame`

```cpp
bool writeFrame(int fd, const string &payload) {
    if (payload.size() > MAX_MSG) return false;
    return writeAll(fd, makeFrame(payload));
}

bool readFrame(int fd, string &payload) {
    string header;
    if (!readExactly(fd, HEADER_LEN, header)) return false;
    uint32_t len = readU32(header, 0);
    if (len > MAX_MSG) return false;  // never trust a length from the network
    return readExactly(fd, len, payload);
}
```

`readFrame` does the two-step read from the framing lesson: **first the
4-byte header, then exactly `len` more bytes.** Because `readExactly` waits
until everything arrives, the byte-stream problem simply disappears here.

## Header additions (the final `protocol.h`)

At the end of the header:

```cpp
// Blocking helpers used by the client and the load tester.
int connectToServer();  // returns the socket, or -1 on failure
bool writeFrame(int fd, const string &payload);
bool readFrame(int fd, string &payload);
```

`writeAll` and `readExactly` aren't in the header: only `protocol.cpp` uses
them.

## Testing real I/O with `socketpair()`

How do we test socket code without starting a server? `socketpair()` creates
**two already-connected sockets** in one call. Whatever you write into one
comes out of the other:

```cpp
int fds[2];
socketpair(AF_UNIX, SOCK_STREAM, 0, fds);   // fds[0] <──connected──> fds[1]
```

`AF_UNIX` means a local socket with no IP address involved, but it's still a
byte stream with the same `read`/`write` behavior.

:::task Finish the protocol
1. `protocol.cpp`: add the includes `<arpa/inet.h>`, `<netinet/tcp.h>` and
   `<unistd.h>` after `#include "protocol.h"`, then add `connectToServer`,
   `writeAll`, `readExactly`, `writeFrame` and `readFrame` at the end.
2. `protocol.h`: add the three declarations above.
3. `test_protocol.cpp`: add `<sys/socket.h>` and `<unistd.h>` includes and
   this test, then call it last from `main`:

```cpp
void testFrameIoOverSocketpair() {
    int fds[2];  // two sockets already connected to each other
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, fds) == 0);

    assert(writeFrame(fds[0], "ping"));
    string got;
    assert(readFrame(fds[1], got));
    assert(got == "ping");

    close(fds[0]);
    close(fds[1]);
    cout << "testFrameIoOverSocketpair: OK" << endl;
}
```

```bash
$ c++ -std=c++17 -Wall test/test_protocol.cpp src/protocol.cpp -o build/test_protocol
$ build/test_protocol
```
:::

```output
testU32Roundtrip: OK
testRequestRoundtrip: OK
testRequestRejectsTruncated: OK
testResponseRoundtripWithData: OK
testResponseRoundtripStatusOnly: OK
testTryParseFrame: OK
testTryParseFrameRejectsOversized: OK
testFrameIoOverSocketpair: OK
All protocol tests passed.
```

:::solution These are the final project files
@include ../src/protocol.h
@include ../src/protocol.cpp
@include ../test/test_protocol.cpp
:::

:::quiz In `testFrameIoOverSocketpair`, why doesn't `readFrame` wait forever?
`writeFrame` has already put all 8 bytes (4 header + "ping") into the socket
pair before `readFrame` runs. Each `read` inside `readExactly` finds data
waiting and returns immediately.
:::

:::recap
- `writeAll` / `readExactly` loop until every byte is transferred.
- `connectToServer()` = socket + `TCP_NODELAY` + connect. Returns -1 instead of dying.
- `writeFrame` sends `[len][payload]` in one go. `readFrame` reads the header, checks it, then reads exactly `len` bytes.
- `socketpair()` gives two connected sockets for testing I/O without a server.
- 🎉 **The protocol is complete.** Next: a server that can handle many clients at once.
:::
