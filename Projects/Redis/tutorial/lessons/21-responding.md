---
title: Parsing requests, queueing replies, and the client
module: The event-loop server
time: 50 min
---

:::goal
Close the loop. The server will cut complete frames out of `incoming`, parse
each request, add a framed reply to `outgoing`, and write it back when the
socket is writable. Then you'll write the real **`client.cpp`** (final
version) to talk to it. For now every command gets the reply "error"; real
commands arrive next lesson.
:::

## A placeholder `runCommand`

So we can test the plumbing first, every command is "unknown":

```cpp
// For now every command is "unknown". The real commands come in the next lesson.
string runCommand(const vector<string> &args) {
    return encodeResponse(RES_ERR);
}
```

It takes the parsed command and returns the **response payload**.

## `handleRequests`: process every complete frame

```cpp
// Handles every complete request in incoming (a client may send several at once).
void handleRequests(Conn *conn) {
    while (true) {
        size_t len = 0;
        FrameResult r = tryParseFrame(conn->incoming, len);
        if (r == FRAME_INCOMPLETE) return;  // wait for more bytes

        vector<string> args;
        if (r == FRAME_TOO_BIG || !parseRequest(conn->incoming.substr(HEADER_LEN, len), args)) {
            conn->wantClose = true;  // garbage: hang up
            return;
        }
        conn->outgoing += makeFrame(runCommand(args));
        conn->incoming.erase(0, HEADER_LEN + len);  // done with this request
    }
}
```

Trace it with a buffer holding **one and a half** requests:

```text
incoming: [frame A (29 bytes)][first 10 bytes of frame B]
 loop 1: COMPLETE → parse A → reply added to outgoing → erase 29 bytes
incoming: [first 10 bytes of frame B]
 loop 2: INCOMPLETE → return     (B stays; the rest arrives in a later read)
```

- If the frame is too big **or** the payload doesn't parse, we can't trust
  anything else the client sends, so we hang up. (When `r` is
  `FRAME_TOO_BIG`, the `||` stops there and `parseRequest` never runs.)
- `incoming.substr(HEADER_LEN, len)` is the payload: the `len` bytes after the
  4-byte header.
- Only after handling the request do we `erase` it. Leftover bytes, the start
  of the next request, stay safely in the buffer.

:::why Why a `while` loop instead of handling one request per read?
A client may send several requests **without waiting for replies**. This is
called **pipelining**, and it's a big speed trick that real Redis clients use.
They can all arrive in a single `read()`. If we handled only one, the others
would sit in `incoming`, and since no new data is coming, `poll` would never
wake us for them: the client would hang forever. **Treat the input as a
stream: keep going until there's nothing complete left.**
:::

## Reading (final version)

`handleRead` now drops the debug print, processes requests, and decides
whether there's something to send:

```cpp
void handleRead(Conn *conn) {
    char buf[64 * 1024];
    int n = read(conn->fd, buf, sizeof(buf));
    if (n < 0 && errno == EAGAIN) return;  // nothing to read after all
    if (n <= 0) {
        conn->wantClose = true;  // error, or the client hung up (n == 0)
        return;
    }
    conn->incoming.append(buf, n);
    handleRequests(conn);
    conn->wantWrite = !conn->outgoing.empty();
}
```

## Writing: `handleWrite`

```cpp
void handleWrite(Conn *conn) {
    int n = write(conn->fd, conn->outgoing.data(), conn->outgoing.size());
    if (n < 0 && errno == EAGAIN) return;  // socket is full, try later
    if (n < 0) {
        conn->wantClose = true;
        return;
    }
    conn->outgoing.erase(0, n);  // write() may have sent only part of it
    conn->wantWrite = !conn->outgoing.empty();
}
```

`write()` on a non-blocking socket may accept only **part** of the data. We
erase exactly what it took, and keep `wantWrite` on until `outgoing` is empty.

## The loop asks for `POLLOUT` only when needed

```cpp
short events = POLLIN;
if (conn->wantWrite) events |= POLLOUT;   // |= adds the POLLOUT bit
fds.push_back({conn->fd, events, 0});
```

and handles it after reading:

```cpp
if (ready & POLLIN) handleRead(conn);
if ((ready & POLLOUT) && !conn->wantClose) handleWrite(conn);
if (conn->wantClose || (ready & (POLLERR | POLLHUP))) {
    close(conn->fd);
    conns[conn->fd] = nullptr;
    delete conn;
}
```

## One more line: ignore `SIGPIPE`

At the top of `main`:

```cpp
signal(SIGPIPE, SIG_IGN);  // writing to a closed socket: return an error, don't kill us
```

:::why What's SIGPIPE and why ignore it?
If you `write()` to a connection the other side has already closed, Unix
sends your process the **SIGPIPE** signal, whose default action is to
**kill the program instantly**. A client disconnecting at the wrong moment
would crash the whole server! Ignoring the signal makes `write()` simply fail
with `-1`, which `handleWrite` treats as "close this connection". (Needs
`#include <signal.h>`.)
:::

## The real client: `src/client.cpp`

The client turns its command-line arguments into a request, sends one frame,
reads one frame, and prints the result.

:::cpp `argc` and `argv`
When you run `build/client set foo bar`, the OS passes the words to `main`:
`argc` = 4 (the count) and `argv` = an array of C strings:
`argv[0]` = `"build/client"`, `argv[1]` = `"set"`, `argv[2]` = `"foo"`,
`argv[3]` = `"bar"`. So the command is `argv[1]` up to `argv[argc - 1]`, and
a loop copies those into a `vector<string>`.
:::

Read it top to bottom; every line uses something you've already built:

@include ../src/client.cpp

- `encodeRequest` builds the payload. Anything over 4096 bytes is refused.
- `connectToServer()` returns `-1` if no server is running.
- `writeFrame` sends, `readFrame` waits for the reply.
- `parseResponse` splits the reply into status and data. For `RES_OK` we
  print the data, or `OK` if there was none.

:::task Make the server reply, and write the client
1. `server.cpp`: add `#include <signal.h>`. Add `runCommand` (placeholder)
   **above** the `Conn` struct, then `handleRequests`, the final
   `handleRead`, and `handleWrite` below it. Update `main`:
   `signal(SIGPIPE, SIG_IGN);` first, `POLLOUT` when `wantWrite`, the
   `handleWrite` call, and remove the debug prints.
2. Write `src/client.cpp` (the final version shown above).
3. Build both:

```bash
$ c++ -std=c++17 -Wall src/server.cpp src/protocol.cpp -o build/server
$ c++ -std=c++17 -Wall src/client.cpp src/protocol.cpp -o build/client
$ build/server
```

4. In terminal 2:

```bash
$ build/client hello
$ build/client get foo
$ build/client
```
:::

```output
(error) unknown command or wrong number of arguments
(error) unknown command or wrong number of arguments
usage: build/client <cmd> [args...]
```

The full round trip works: the client encoded a request, framed it and sent it.
The server buffered it, cut out the frame, parsed it, built a framed error
reply and wrote it back. The client read and decoded it.

:::hint Hint: the server's order of functions
C++ needs things declared before use. A working order is: includes →
`die` → `setNonBlocking` → `runCommand` → `Conn` → `handleRequests` →
`handleRead` → `handleWrite` → `makeListener` → `main`.
:::

:::solution
@include code/e-server/s3/src/server.cpp
:::

:::quiz Why does the client not need an event loop?
It has exactly **one** connection and one thing to do: send, then wait for
the reply. Waiting is perfect for that. Event loops are for juggling many
connections at once.
:::

:::recap
- `handleRequests` loops: `tryParseFrame` → `parseRequest` → `runCommand` → `makeFrame` into `outgoing` → `erase`.
- Bad input → `wantClose`. Incomplete input → wait.
- `handleWrite` writes what it can, erases it, and keeps `wantWrite` while `outgoing` is non-empty.
- `POLLOUT` is requested **only** when `wantWrite`. `SIGPIPE` is ignored.
- `client.cpp`: `argv` → `encodeRequest` → `connectToServer` → `writeFrame` → `readFrame` → `parseResponse` → print.
:::
