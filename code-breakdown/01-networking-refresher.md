# 01 — Networking Refresher

Everything from computer networks that this project uses, from zero. Every
section ends by pointing at the line of code where the idea shows up.

---

## 1. The big picture: layers

When two programs talk over a network, the work is split into layers. Each
layer only talks to the one directly above and below it.

| Layer | Job | Example | Who handles it here |
|---|---|---|---|
| Application | What the bytes *mean* | HTTP, Redis's RESP, **our protocol** | **Our code** (`protocol.cpp`, `server.cpp`) |
| Transport | Deliver bytes between two *programs* reliably | **TCP**, UDP | The OS kernel |
| Network | Deliver packets between two *machines* | **IP** | The OS kernel |
| Link | Deliver frames on one physical link | Ethernet, Wi-Fi, loopback | The OS kernel / hardware |

The key point: **our code only works at the application layer.** We hand
bytes to the kernel through *sockets*, and the kernel does TCP and IP for us.
We never build packets, compute checksums or retransmit anything.

---

## 2. IP addresses and loopback

An **IP address** identifies a machine (more precisely, a network
interface). IPv4 addresses are 32-bit numbers written as four bytes, like
`192.168.1.10`.

Special addresses you'll see:

| Address | Meaning |
|---|---|
| `127.0.0.1` | **Loopback** ("localhost"). Traffic never leaves your machine; the kernel hands it straight from sender to receiver. |
| `0.0.0.0` | When a server binds to this, it means "accept connections on **every** interface" (Wi-Fi, Ethernet, loopback). |

Our server binds to `127.0.0.1` (`INADDR_LOOPBACK` in the code), so **only
programs on the same computer can connect**. Nobody on your Wi-Fi can reach
it. That's a safe default for a toy database with no password.

> Code: `server.cpp:187` and `protocol.cpp:155` — `htonl(INADDR_LOOPBACK)`.

---

## 3. Ports and the 4-tuple

An IP address finds the machine; a **port** (a 16-bit number, 0–65535)
finds the program on that machine. Think of the IP as a building address and
the port as the flat number.

- Our server listens on **port 1234** (`kServerPort`).
- Well-known services use fixed ports: HTTP 80, HTTPS 443, SSH 22, real Redis 6379.
- A **client** doesn't pick its port. The kernel assigns a temporary
  **ephemeral port** (on macOS, from 49152–65535) when you call `connect()`.

A TCP connection is uniquely identified by **four values** (the *4-tuple*):

```
(client IP, client port, server IP, server port)
 127.0.0.1   52311       127.0.0.1   1234      <- connection A
 127.0.0.1   52312       127.0.0.1   1234      <- connection B
```

This is how 200 benchmark clients can all talk to the same server port at
once: each has a different client port, so each is a different connection.

---

## 4. TCP vs UDP

| | TCP | UDP |
|---|---|---|
| Connection | Yes (handshake first) | No, just send |
| Reliable (lost data re-sent) | Yes | No |
| Ordered | Yes | No |
| Shape of data | **Byte stream** (no message boundaries) | Separate datagrams (boundaries kept) |
| Used by | Web, databases, SSH, **this project** | DNS, video calls, games |

**Why TCP here?** A database must never silently lose or reorder a `set`.
TCP gives us that for free. The price is that TCP is a *stream*, which we
deal with in section 6.

> Code: `SOCK_STREAM` in `socket(AF_INET, SOCK_STREAM, 0)` means TCP
> (`SOCK_DGRAM` would be UDP). `AF_INET` means IPv4.

---

## 5. TCP connection lifecycle

### Opening: the 3-way handshake

```
 client                          server
   │  ──── SYN ─────────────────►  │   "I want to connect"
   │  ◄─── SYN + ACK ───────────  │   "OK, I heard you"
   │  ──── ACK ─────────────────►  │   "I heard you too"
   │        connection open        │
```

The kernel does this for us:
- The client's `connect()` sends the SYN and returns once the handshake is done.
- On the server, the kernel completes handshakes **by itself** and puts the
  finished connections in a queue (the *backlog*). `accept()` just takes one
  from that queue.

### Sending data

Each chunk of data is acknowledged (ACK). If an ACK doesn't arrive in time,
the sender's kernel re-sends. Our code never sees any of this.

### Closing: FIN and TIME_WAIT

```
 client                          server
   │  ──── FIN ─────────────────►  │   client called close()
   │  ◄─── ACK ─────────────────  │
   │  ◄─── FIN ─────────────────  │   server called close()
   │  ──── ACK ─────────────────►  │
   │  TIME_WAIT (30s on macOS)     │
```

- When the other side closes, `read()` returns **0**. That means
  **EOF** ("end of file": no more data will ever come).
- Whoever closes **first** (the *active closer*) keeps the connection in a
  **TIME_WAIT** state for a while (30 s on macOS, 60 s on Linux), so stray
  late packets from the old connection can't be mistaken for a new one.

**Example from this project:** `client.cpp` calls `close(fd)` after reading
the reply, so the *client* closes first. The integration test runs 10,000
clients, which leaves up to 10,000 client ports sitting in TIME_WAIT.
That's fine because macOS has about 16,000 ephemeral ports.

**Why the server uses `SO_REUSEADDR`:** if the server is killed and restarted,
its old connections may still be in TIME_WAIT on port 1234. Without
`SO_REUSEADDR`, `bind()` would fail with "Address already in use" for up to
a minute. With it, you can restart immediately.

> Code: `server.cpp:182`.

### Abrupt close: RST

If a program crashes or closes a socket with unread data, the kernel may
send a **RST** (reset) instead of a FIN. The other side's next `read()` or
`write()` then fails with an error such as `ECONNRESET`.

---

## 6. TCP is a byte stream (why framing exists)

This is the most important idea for this project.

TCP guarantees the **bytes** arrive in order. It does **not** keep the
boundaries between your `write()` calls. The kernel can split or merge them.

**Example.** The client sends two requests, 29 bytes and 25 bytes:

```
client:  write(29 bytes)   write(25 bytes)
```

The server's `read()` calls might return any of these:

```
read -> 54 bytes                   (both merged)
read -> 10 bytes, read -> 44 bytes (first one split)
read -> 29 bytes, read -> 25 bytes (lucky, looks like messages)
```

So the receiver needs a rule to find where one message ends. Common options:

| Method | How | Used by |
|---|---|---|
| Delimiter | End each message with `\r\n` | HTTP headers, RESP |
| **Length prefix** | Put the message length first | **This project**, many binary protocols |
| Fixed size | Every message is N bytes | Rare |

We use a **4-byte length prefix**: `[length][payload]`. The receiver reads
4 bytes, learns the length, then waits until that many more bytes have
arrived. This is called a **frame**.

> Code: `tryParseFrame` (`protocol.cpp:130`) and `readFrame`
> (`protocol.cpp:172`).

---

## 7. Sockets and file descriptors

A **socket** is the kernel object you use to do networking. In Unix,
everything you can read or write (files, pipes, sockets, the terminal) is
represented by a small integer called a **file descriptor (fd)**.

- `0`, `1`, `2` are stdin, stdout, stderr.
- New fds get **the lowest free number**. So the first socket is usually
  `3`, the next `4`, and when fd `5` is closed the next new one reuses `5`.

That last point is why the server stores connections in a plain vector
indexed by fd: fds are small and dense, so a vector is faster and simpler
than a hash map.

### The system calls

A **system call (syscall)** is a function that asks the kernel to do
something. Each one costs roughly 0.1–1 µs because the CPU switches into
kernel mode.

**Server:**

```
socket()      create a socket                     -> listenFd
setsockopt()  set options (SO_REUSEADDR)
bind()        attach it to 127.0.0.1:1234
listen()      mark it as a listening socket, create the backlog queue
loop:
  accept()    take one finished connection        -> a NEW fd for that client
  read()/write() on that new fd
  close()
```

**Client:**

```
socket()      create a socket
connect()     do the handshake with 127.0.0.1:1234
write()/read()
close()
```

**Important:** the listening socket is only used for accepting. Every
accepted client gets **its own new fd**, and all data goes through that one.

```
listenFd (3)  ── accept() ──► fd 4  (client A)
               ── accept() ──► fd 5  (client B)
               ── accept() ──► fd 6  (client C)
```

---

## 8. Kernel buffers: what read() and write() really do

Every TCP socket has two buffers inside the kernel:

```
   your program                  kernel                        network
   write(fd, ...) ──copy──► [ send buffer ] ──TCP sends──►
   read(fd, ...)  ◄──copy── [ receive buffer ] ◄──TCP receives──
```

- `write()` **does not send over the network**. It copies your bytes into
  the send buffer and returns. The kernel sends them later.
- `read()` copies whatever is already in the receive buffer.

Consequences:

1. **Partial reads.** `read(fd, buf, 1000)` may return 10 if only 10 bytes
   have arrived. You must loop or buffer.
2. **Partial writes.** If the send buffer only has room for 300 bytes,
   `write(fd, buf, 1000)` returns 300. You must write the rest later.
3. **Return values:** `> 0` bytes transferred, `0` EOF (for `read`), `-1`
   error (check `errno`).

> Code: `readFull`/`writeAll` loop until done (`protocol.cpp:24-46`).
> The server instead keeps leftovers in `Conn::incoming`/`outgoing`.

---

## 9. Blocking vs non-blocking sockets

By default, sockets are **blocking**:
- `read()` with an empty receive buffer **puts your thread to sleep** until data arrives.
- `write()` with a full send buffer sleeps until there's room.
- `accept()` with no pending connection sleeps.

For a client that talks to one server, that's perfect (our client and
benchmark use blocking sockets).

For a server with many clients, it's a disaster. If the server sleeps in
`read()` on client A, clients B, C, D… get no service until A sends
something. **One slow client stalls everyone.**

A **non-blocking** socket (flag `O_NONBLOCK`) never sleeps. If the call
can't make progress, it returns `-1` immediately with `errno` set to
`EAGAIN` (also named `EWOULDBLOCK`), meaning "nothing to do right now, try
later".

> Code: `setNonBlocking` (`server.cpp:25`), and the `EAGAIN` checks in
> `handleRead`/`handleWrite` (`server.cpp:151`, `:165`).

---

## 10. Serving many clients: I/O multiplexing

With non-blocking sockets, how do we know *when* to try again? Checking
every socket in a loop would burn 100% CPU. Instead we ask the kernel:
**"here are my sockets; put me to sleep until at least one is ready."**
This is **I/O multiplexing**.

### The options

| Call | OS | How it works | Cost per call |
|---|---|---|---|
| `select()` | All | Bitmap of fds, max 1024 fds | O(all fds) |
| **`poll()`** | All POSIX (**macOS**, Linux) | Array of `pollfd` structs, passed in every call | O(all fds) |
| `epoll` | Linux only | Register fds once, kernel keeps the list, returns only ready ones | O(ready fds) |
| `kqueue` | macOS/BSD | Same idea as epoll | O(ready fds) |

**This project uses `poll()`**. It works on macOS and is simple. Its
weakness: every call passes *all* fds and the kernel checks *all* of them.
At 200 connections that's cheap. At 50,000 connections mostly sitting idle,
it wastes most of its time, and that's the problem epoll/kqueue solve (the
famous **"C10K problem"**: handling 10,000 concurrent connections).

### How `poll()` works

```cpp
struct pollfd {
    int   fd;       // which socket
    short events;   // what you want to know about (you fill this in)
    short revents;  // what actually happened (kernel fills this in)
};
int poll(pollfd *fds, nfds_t n, int timeout_ms);  // -1 = wait forever
```

| Flag | Meaning |
|---|---|
| `POLLIN` | Readable: data arrived, **or** the peer closed (read will return 0). On a **listening** socket: a new connection is waiting for `accept()`. |
| `POLLOUT` | Writable: the send buffer has room. |
| `POLLERR` | An error happened on the socket. Always reported, even if not requested. |
| `POLLHUP` | The connection was hung up. Always reported. |

**Example round.** Server has fds 3 (listener), 4, 5:

```
we pass:    {3, POLLIN}  {4, POLLIN}  {5, POLLIN|POLLOUT}
poll sleeps... client on fd 4 sends a request ...
kernel returns: revents = {0, POLLIN, POLLOUT}
we then:    read from 4, write to 5
```

### Why only ask for POLLOUT sometimes

A socket's send buffer almost always has room, so if we asked for `POLLOUT`
all the time, `poll()` would return instantly on every loop and we'd spin
at 100% CPU. We only ask when we actually have bytes waiting to be written
(`wantWrite`).

### Level-triggered vs edge-triggered

- **Level-triggered** (poll, select, epoll default): "tell me *while* the
  socket is ready". If you only read half the data, the next `poll()`
  reports it again. Forgiving.
- **Edge-triggered** (epoll with `EPOLLET`): "tell me *when it becomes*
  ready". You must drain everything, or you won't be told again. Faster,
  easier to get wrong.

`poll()` is level-triggered. That's why the server can accept **one**
connection per loop and still be fine: if more are waiting, the next
`poll()` returns immediately and reports the listener again.

### Event loop vs thread per client

| | Thread per client | Event loop (this project) |
|---|---|---|
| Code | Simple, blocking calls | Must keep per-client state (buffers, flags) |
| Memory | A stack per thread (often 512 KB–8 MB) | A few buffers per client |
| Shared data | Needs locks | None needed, one thread |
| Scales to | Hundreds–low thousands | Tens of thousands (with epoll/kqueue) |

Real Redis, nginx and Node.js all use event loops.

---

## 11. Byte order (endianness)

A 4-byte integer can be stored in memory two ways. Take the number
`25` (hex `0x00000019`):

```
little-endian (x86, Apple M-series, most ARM):  19 00 00 00
big-endian    ("network byte order"):           00 00 00 19
```

The rule in networking is that protocol headers (IP, TCP, port numbers) use
**big-endian**, called **network byte order**. So the socket API needs
conversions:

| Function | Meaning |
|---|---|
| `htons(x)` | **h**ost **to** **n**etwork, **s**hort (16-bit, used for ports) |
| `htonl(x)` | **h**ost **to** **n**etwork, **l**ong (32-bit, used for IPv4 addresses) |
| `ntohs`, `ntohl` | The reverse |

On a little-endian Mac, `htons(1234)` swaps the two bytes. On a big-endian
machine it does nothing.

**A quirk of this project:** our *own* protocol (the length prefixes) is
written in **host order** with a plain `memcpy`, not network order. That
works because every machine you'll realistically use is little-endian, but a
big-endian client and a little-endian server would misread each other. A
production protocol would pick one order explicitly. Good interview point.

> Code: `htons(kServerPort)` (`server.cpp:186`), `readU32`/`appendU32`
> (`protocol.cpp:14-22`).

---

## 12. Nagle's algorithm and TCP_NODELAY

Sending a TCP packet for every tiny `write()` wastes bandwidth (each packet
has at least 40 bytes of headers). **Nagle's algorithm** says: if you have
sent data that hasn't been ACKed yet, hold back new small writes and batch
them.

Combined with **delayed ACK** (the receiver waits a bit before ACKing, hoping
to piggy-back the ACK on a reply), Nagle can add tens of milliseconds to a
request/response exchange. The classic trap: a client writes the header and
the body in **two** `write()` calls. The second waits for the ACK of the
first, and the ACK is delayed.

`TCP_NODELAY` turns Nagle off: send small writes immediately. Latency-critical
clients (databases, games) usually set it.

> Code: `connectToServer` sets `TCP_NODELAY` (`protocol.cpp:150`). Also,
> `writeFrame` builds the header and payload into one buffer and sends them
> in **one** `write()`, which avoids the trap anyway.

---

## 13. When the other side goes away

| Situation | What our code sees |
|---|---|
| Peer closed normally (FIN) | `read()` returns 0 → close our side |
| Peer crashed / reset (RST) | `read()`/`write()` returns -1 (`ECONNRESET`), or `poll` reports `POLLERR`/`POLLHUP` |
| We `write()` to a socket the peer already closed | The kernel sends our process the **SIGPIPE** signal, whose default action is **to kill the process** |

That last one would let any client crash the whole server by disconnecting
at the wrong moment. So the server runs `signal(SIGPIPE, SIG_IGN)` (ignore
it). Now the `write()` just fails with `EPIPE`, and we close that one
connection.

> Code: `server.cpp:201`.

**Half-close:** TCP lets a client say "I'm done sending" (`shutdown(fd,
SHUT_WR)`) while still reading replies. Our server treats that EOF as "close
everything", so replies not yet written are dropped. A listed limitation.

---

## 14. The listen backlog

Between the handshake finishing and your `accept()` call, completed
connections wait in a kernel queue. `listen(fd, backlog)` sets its maximum
length. `SOMAXCONN` means "the system maximum" (128 on macOS, 4096 on recent
Linux). If the queue is full, new clients' connection attempts are dropped
or delayed until there's room.

> Code: `server.cpp:191`.

---

## 15. Latency, throughput and pipelining

- **Latency:** time for one request's round trip (send → reply received).
- **Throughput:** requests completed per second across all clients.
- **Round-trip time (RTT):** the network part of latency. On loopback it's
  a few microseconds; across a continent it's ~50–100 ms.

**Little's law** connects them for a closed system (each client waits for
its reply before sending again):

```
clients in flight = throughput × average latency
200               = 184,000/s  × 1.09 ms          ✓ matches our benchmark
```

So with 200 clients, most of the ~1 ms latency is **queueing** (waiting
behind the other 199 requests), not the server being slow at any one
request.

**Pipelining:** a client sends several requests without waiting for replies.
TCP keeps them in order, so replies come back in the same order. Our server
supports this: `handleRequests` loops until no complete frame is left in
the buffer.

---

## 16. errno and EINTR

System calls return `-1` on failure and store the reason in the global
variable `errno`. Common values here:

| errno | Meaning | Our reaction |
|---|---|---|
| `EAGAIN` / `EWOULDBLOCK` | Non-blocking call can't proceed now | Try again after the next `poll()` |
| `EINTR` | A signal interrupted the call | Just call it again |
| `EPIPE` | Wrote to a closed connection | Close the connection |
| `ECONNRESET` | Peer reset the connection | Close the connection |
| `EADDRINUSE` | `bind()` failed: port taken | Server exits with an error |
| `ECONNREFUSED` | `connect()`: nobody listening on that port | Client prints the error |

`perror("bind()")` prints your message plus the text for the current
`errno`, e.g. `bind(): Address already in use`.

---

## 17. Quick glossary

| Term | One-line meaning |
|---|---|
| Socket | Kernel object for network I/O, used through an fd |
| fd | Small integer handle for an open file/socket |
| Listening socket | Only accepts new connections |
| Connected socket | Carries one client's data |
| Loopback | 127.0.0.1, traffic stays inside the machine |
| Ephemeral port | Temporary client-side port chosen by the kernel |
| Frame | One length-prefixed message |
| Non-blocking | Calls return `EAGAIN` instead of sleeping |
| Event loop | One thread that waits for readiness and handles whatever is ready |
| Level-triggered | Readiness is reported as long as it's true |
| Backpressure | Slowing a sender down when the receiver can't keep up |
| Pipelining | Sending several requests before reading replies |
| Syscall | A call into the OS kernel |
