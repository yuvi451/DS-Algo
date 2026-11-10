---
title: Sockets: open a port and accept connections
module: How networks work
time: 50 min
---

:::goal
Write your first real network program: a server that **listens on
127.0.0.1:1234** and **accepts** incoming connections. You'll learn
`socket()`, `setsockopt()`, `bind()`, `listen()` and `accept()`, the
`sockaddr_in` address struct, and why `htons()` exists. This is CodeCrafters'
first stage, *"Bind to a port"*.
:::

## What is a socket?

A **socket** is the kernel object you use for networking, and your program
refers to it with a **file descriptor**, just like a file. There are two kinds,
and the difference matters a lot:

| | Listening socket | Connection socket |
|---|---|---|
| Created by | `socket()` + `bind()` + `listen()` | `accept()` on the server, `connect()` on the client |
| Job | Wait for new clients, like a receptionist | Carry data with **one** client |
| Can you `read`/`write` it? | No | Yes |
| How many | One per server | One per connected client |

```text
 listening fd 3 ──accept()──► fd 4  (talks to client A)
                ──accept()──► fd 5  (talks to client B)
                ──accept()──► fd 6  (talks to client C)
```

:::analogy
The listening socket is a **receptionist at the front desk**. When a visitor
arrives, the receptionist doesn't chat with them. They hand the visitor over
to a new **staff member** (a connection socket) and go back to waiting at the
desk.
:::

## The server recipe

```text
socket()      → get a new, blank socket fd
setsockopt()  → set an option (SO_REUSEADDR)
bind()        → attach it to 127.0.0.1:1234
listen()      → turn it into a listening socket
loop:
  accept()    → wait for a client, get a NEW fd for that client
  ...talk on that fd...
  close()     → hang up on that client
```

Let's go through each call.

### 1. `socket()`: get a socket

```cpp
int fd = socket(AF_INET, SOCK_STREAM, 0);
if (fd < 0) die("socket()");
```

- `AF_INET` = IPv4 addresses (`AF_INET6` would be IPv6).
- `SOCK_STREAM` = a byte stream, i.e. **TCP** (`SOCK_DGRAM` would be UDP).
- `0` = "pick the default protocol for this combination", which is TCP.
- Returns an fd, or `-1` on failure.

`die` is a tiny helper we write ourselves: print what failed and why, then
quit.

```cpp
void die(const string &what) {
    cerr << what << " failed: " << strerror(errno) << endl;
    exit(1);
}
```

`cerr` is like `cout`, but for error messages. `exit(1)` (from `<cstdlib>`)
ends the program right away.

### 2. `setsockopt()`: allow quick restarts

```cpp
int yes = 1;
setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
```

This turns the option `SO_REUSEADDR` **on** (value `1`). Without it, if you
stop your server and immediately restart it, `bind()` fails with **"Address
already in use"** for up to a minute.

:::why Why would the port still be "in use" after the server stopped?
When a TCP connection closes, the side that closed first keeps a little
memory of it for a while (a state called **TIME_WAIT**, 30–60 seconds), so
that late, stray packets from the old connection can't be confused with a new
one. `SO_REUSEADDR` tells the kernel "let me bind anyway, I know what I'm
doing". **Every server sets it.**
:::

`setsockopt` wants a **pointer** to the value plus its size, because
different options take different types. That's the `&yes, sizeof(yes)`.

### 3. `bind()`: choose the address

First we fill in an address struct:

```cpp
sockaddr_in addr = {};                         // {} = start with all zeros
addr.sin_family = AF_INET;                     // it's an IPv4 address
addr.sin_port = htons(1234);                   // port, big-endian
addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK); // 127.0.0.1, big-endian
```

`sockaddr_in` ("socket address, internet") holds an IPv4 address + port.
`INADDR_LOOPBACK` is the constant for `127.0.0.1`.

:::net `htons` and `htonl`: host to network byte order
Remember endianness? The socket API wants port and IP in **big-endian**
("network order"), but your CPU is little-endian. These functions convert:

- `htons` = **H**ost **TO** **N**etwork **S**hort (16-bit, for ports)
- `htonl` = **H**ost **TO** **N**etwork **L**ong (32-bit, for IPv4 addresses)

On a little-endian machine they swap the bytes. On a big-endian one they do
nothing. **Forget `htons` and your server listens on the wrong port**:
`1234` = `0x04D2`, and byte-swapped that's `0xD204` = port 53764!
:::

Now attach the socket to that address:

```cpp
if (::bind(fd, (sockaddr *)&addr, sizeof(addr)) != 0) die("bind()");
```

:::cpp Why `(sockaddr *)&addr`?
`bind()` is an old C function written to accept *any* kind of address (IPv4,
IPv6, Unix…), so its parameter type is a generic `sockaddr *`. We have a
`sockaddr_in`. The cast `(sockaddr *)` tells the compiler: "treat this
pointer as that other pointer type. Trust me." The `sizeof(addr)` tells
`bind` how many bytes the real struct has. It's the same kind of cast as
`(char *)&v` from the bytes lesson.
:::

:::cpp Why `::bind` and not `bind`?
Remember the warning from the multi-file lesson: with `using namespace std;`,
plain `bind` can mean the unrelated `std::bind`. `::bind` means the operating
system's one.
:::

### 4. `listen()`: start accepting

```cpp
if (listen(fd, SOMAXCONN) != 0) die("listen()");
```

From now on, **the kernel itself** completes the TCP handshake with any
client that connects, and puts the finished connection in a queue (the
*backlog*). `SOMAXCONN` is "the biggest queue the OS allows".

### 5. `accept()`: take one connection from the queue

```cpp
int connFd = accept(fd, nullptr, nullptr);
```

Waits until a client is in the queue, then returns a **new fd** for that
connection. The two `nullptr`s mean "I don't need the client's address".

:::net What's the "handshake"?
Before any data flows, TCP does a 3-step greeting called the
**three-way handshake**: client says *SYN* ("let's talk"), server says
*SYN-ACK* ("sure"), client says *ACK* ("great"). The kernel does all of it.
`connect()` on the client returns once it's done, and `accept()` on the server
just picks up connections that already finished it.
:::

:::task Bind to a port
Write `scratch/listen_server.cpp`:

1. Includes: `<cerrno>`, `<cstdlib>`, `<cstring>`, `<iostream>`, `<string>`,
   and the operating-system headers `<arpa/inet.h>` (sockets, `htons`/`htonl`)
   and `<unistd.h>` (`close`). Then `using namespace std;`.
2. Write `die()`.
3. In `main`: create the socket, set `SO_REUSEADDR`, bind to `127.0.0.1:1234`,
   listen. Print `listening on 127.0.0.1:1234 (listening fd = N)`.
4. Loop forever: `accept()`. If it fails (`< 0`) `continue`. Otherwise print
   `accepted a connection, it got fd N` and immediately `close()` it.

Run it in **terminal 1**:

```bash
$ c++ -std=c++17 -Wall scratch/listen_server.cpp -o build/listen_server
$ build/listen_server
```

In **terminal 2**, connect twice. `nc -z` connects and immediately hangs up:

```bash
$ nc -z 127.0.0.1 1234
$ nc -z 127.0.0.1 1234
```
:::

```output
listening on 127.0.0.1:1234 (listening fd = 3)
accepted a connection, it got fd 4
accepted a connection, it got fd 4
```

Both connections got **fd 4**: we closed the first one, so its number was
free again. Terminal 2 prints something like
`Connection to 127.0.0.1 port 1234 [tcp/*] succeeded!` each time. Stop the
server with **Ctrl + C**.

:::hint Hint: `bind() failed: Address already in use`
Another program (perhaps an `nc -l 1234` from before) is on port 1234. Stop
it, or find it with `lsof -iTCP:1234 -sTCP:LISTEN`.
:::

:::solution
@include code/c-sockets/listen_server.cpp title=scratch/listen_server.cpp
:::

:::quiz What would happen if you removed `htons()` and wrote `addr.sin_port = 1234;`?
The server would still start, but on the **wrong port** (53764 on a
little-endian machine), and `nc -z 127.0.0.1 1234` would fail with
"connection refused". Byte order bugs are silent, so always convert ports
and IPs.
:::

:::quiz Why does the listening socket get fd 3?
fds 0, 1 and 2 (stdin, stdout, stderr) are already open. The kernel always
hands out the lowest free number.
:::

:::recap
- Server recipe: `socket → setsockopt(SO_REUSEADDR) → bind → listen → accept loop`.
- `sockaddr_in` holds an IPv4 address + port, **in big-endian**: use `htons`/`htonl`.
- `(sockaddr *)&addr` adapts our IPv4 struct to the generic C API. Write `::bind`.
- The listening socket only accepts. Each `accept()` returns a **new fd** per client.
:::
