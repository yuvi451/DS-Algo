---
title: A server that talks back
module: First server & client
time: 30 min
---

:::goal
Upgrade the listener so it actually **reads** what the client sends and
**writes** a reply: the client says `hello`, the server answers `world`.
Along the way we pull the setup code into a reusable `makeListener()`
function, the same one our final server uses.
:::

## Reading and writing on a connection

Once `accept()` hands us a connection fd, it behaves like a file. `read()`
gets bytes the client sent, `write()` sends bytes back:

```text
  client                               server
    │ ── write("hello") ──────────────► │ read(connFd, buf, 64) → 5 bytes: "hello"
    │ ◄──────────────── write("world") ─│
    │ read → "world"                    │ close(connFd)
```

Here's the conversation function:

```cpp
void talk(int connFd) {
    char buf[64];
    int n = read(connFd, buf, sizeof(buf));   // up to 64 bytes
    if (n < 0) {
        cerr << "read() failed" << endl;
        return;
    }
    cout << "client says: " << string(buf, n) << endl;
    write(connFd, "world", 5);
}
```

- `read` fills `buf` with however many bytes arrived and returns that count.
- `string(buf, n)` turns exactly those `n` bytes into a string we can print.
- `write(connFd, "world", 5)` sends the 5 letters of `world`.

:::warn This code is deliberately naive
It assumes **one `read()` returns the whole message**. That's not
guaranteed with TCP. Two lessons from now you'll watch it fail. For now it's
the simplest possible starting point.
:::

## Refactor: `makeListener()`

`main` was getting long. Let's move the five setup steps into a function
that returns the listening fd. This is (almost) exactly the function in our
final `server.cpp`:

```cpp
int makeListener() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) die("socket()");
    int yes = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));

    sockaddr_in addr = {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(1234);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (::bind(fd, (sockaddr *)&addr, sizeof(addr)) != 0) die("bind()");
    if (listen(fd, SOMAXCONN) != 0) die("listen()");
    return fd;
}
```

:::task Hello → world
Write `scratch/hello_server.cpp`:

1. Copy `die()` and `makeListener()` from above (type them, don't paste!).
2. Write `talk(int connFd)`.
3. `main`: call `makeListener()`, print `listening on 127.0.0.1:1234`, then
   loop forever: `accept`, `talk`, `close`.

**Terminal 1:**

```bash
$ c++ -std=c++17 -Wall scratch/hello_server.cpp -o build/hello_server
$ build/hello_server
```

**Terminal 2:** connect with `nc`, type `hello` and press Enter:

```bash
$ nc 127.0.0.1 1234
hello
```
:::

```output
Terminal 1 (server):
listening on 127.0.0.1:1234
client says: hello

Terminal 2 (nc):
hello
world
```

The empty line after `client says: hello` is the **newline** you typed in
`nc`, which was sent too. `nc` usually exits when the server closes the
connection. If yours doesn't, press Ctrl + C. **Leave the server running** for
the next lesson.

:::hint Hint: the main loop
```cpp
while (true) {
    int connFd = accept(listenFd, nullptr, nullptr);
    if (connFd < 0) continue;
    talk(connFd);
    close(connFd);
}
```
:::

:::solution
@include code/c-sockets/hello_server.cpp title=scratch/hello_server.cpp
:::

:::quiz While one client is connected but hasn't typed anything, a second `nc` connects. Does it get served?
No, not until the first client sends something. The server is stuck inside
`read()` waiting for client 1. It can't `accept()` client 2 meanwhile. This
is the **blocking** problem, and Part 5 solves it with an event loop. Try it!
:::

:::recap
- After `accept()`, `read()`/`write()` on the connection fd move bytes to and from that one client.
- `string(buf, n)` turns the `n` bytes that `read` returned into a string.
- `makeListener()` wraps socket/setsockopt/bind/listen. We'll keep it to the end.
:::
