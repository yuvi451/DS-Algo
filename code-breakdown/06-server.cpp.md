# 06 — `src/server.cpp`

**What it is:** the server program. It has three parts:

1. **Key-value store** (lines 32–106): `Entry`, `KvStore`, `runCommand`,
   built on the `HMap` hashtable.
2. **Connections** (lines 108–196): per-client state and the code that reads
   requests and writes replies without ever blocking.
3. **Event loop** (lines 198–253): `main()`, a single thread that uses
   `poll()` to serve every client.

This is the most important file for interviews. If you understand the event
loop here, you understand how Redis, nginx and Node.js handle many clients
on one thread.

Before reading, it helps to have read [01 — networking refresher](01-networking-refresher.md)
sections 7–10.

---

## Lines 1–18: includes

```cpp
#include <cerrno>    // errno, EAGAIN, EINTR
#include <csignal>   // signal, SIGPIPE
#include <cstdio>    // perror, fprintf
#include <cstdlib>   // exit
#include <memory>    // std::unique_ptr, std::make_unique
#include <optional>
#include <string>
#include <vector>

#include <arpa/inet.h>    // htons, htonl
#include <fcntl.h>        // fcntl, O_NONBLOCK
#include <netinet/in.h>   // sockaddr_in, INADDR_LOOPBACK
#include <poll.h>         // poll, pollfd, POLLIN, POLLOUT...
#include <sys/socket.h>   // socket, bind, listen, accept, setsockopt
#include <unistd.h>       // read, write, close

#include "hashtable.h"
#include "protocol.h"
```

Standard C++ first, then POSIX (the OS API), then our own headers.

---

## Lines 20–23: `die`

```cpp
[[noreturn]] static void die(const char *msg) {
    perror(msg);
    exit(1);
}
```

Print an error and quit. Used only for problems the server can't recover
from (can't create the listening socket, `poll` itself fails).

- `perror("bind()")` prints your text plus a description of the current
  `errno`, e.g. `bind(): Address already in use`.
- `exit(1)` ends the process with status 1 (non-zero = failure).

> **C++ note — `[[noreturn]]`:** tells the compiler this function never
> returns. It can then stop warning about "missing return" in code paths
> that call `die`.

> **C++ note — `static` on a free function:** the function is private to
> this file (same effect as the anonymous namespace in `protocol.cpp`).

---

## Lines 25–30: `setNonBlocking`

```cpp
static void setNonBlocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1 || fcntl(fd, F_SETFL, flags | O_NONBLOCK) == -1) {
        die("fcntl()");
    }
}
```

Switch a socket into **non-blocking mode**.

- `fcntl(fd, F_GETFL)` ("file control, get flags") reads the fd's current
  flags as a bit mask.
- `flags | O_NONBLOCK` turns on the non-blocking bit without touching the others.
- `fcntl(fd, F_SETFL, ...)` writes the flags back.

> **CN refresher — non-blocking sockets:** normally `read()` on a socket
> with no data puts the thread to sleep until data arrives. With
> `O_NONBLOCK`, it instead returns `-1` immediately with `errno = EAGAIN`
> ("try again later").
>
> **Why the server needs this.** Imagine clients A and B are connected. A
> connected but hasn't sent anything yet; B has sent `get foo`. If the
> server did a blocking `read()` on A, it would sleep until A sends
> something, possibly forever, and B would never get its answer. With
> non-blocking sockets plus `poll()` (below), the server only reads from
> sockets that are ready, and never sleeps on any single client.
> See [01 §9](01-networking-refresher.md#9-blocking-vs-non-blocking-sockets).

---

# Part 1: the key-value store

## Lines 34–37: `Entry`

```cpp
struct Entry : HNode {
    std::string key;
    std::string val;
};
```

One stored key-value pair. It **inherits** from `HNode`, so every `Entry`
has `next` and `hcode` inside it, and the hashtable can link it directly.
See the intrusive-node explanation in [04](04-hashtable.h.md#lines-812-hnode-the-intrusive-node).

> **C++ note — `struct Entry : HNode`:** inheritance. With `struct`, it's
> public by default (same as `: public HNode`). A pointer to an `Entry` can
> be used wherever an `HNode*` is expected.

---

## Lines 39–45: the two callbacks for HMap

```cpp
static bool entryEq(const HNode *lhs, const HNode *rhs) {
    return static_cast<const Entry *>(lhs)->key == static_cast<const Entry *>(rhs)->key;
}

static void entryDelete(HNode *node) {
    delete static_cast<Entry *>(node);
}
```

- `entryEq`: the hashtable asks "are these two nodes the same key?" We know
  every node in our map is really an `Entry`, so we convert back and compare
  the key strings.
- `entryDelete`: free a node. We must `delete` it **as an `Entry`** so the
  `key` and `val` strings get destroyed too. Deleting it as a plain `HNode`
  would be undefined behaviour, because `HNode` has no virtual destructor.

> **C++ note — `static_cast<Entry *>(node)` (a downcast):** converts a
> base-class pointer back to the derived class. It's not checked at runtime,
> so it's only correct if the object really is an `Entry`. Here it always
> is, because only `KvStore` inserts into this map.

---

## Lines 47–88: `KvStore`

A thin wrapper that gives the hashtable a string-based API.

### `get` (lines 49–56)

```cpp
    std::optional<std::string> get(std::string_view key) const {
        Entry probe = makeProbe(key);
        HNode *node = map_.lookup(&probe);
        if (!node) {
            return std::nullopt;
        }
        return static_cast<Entry *>(node)->val;
    }
```

1. Build a temporary **probe** `Entry` holding the key and its hash.
2. Ask the map for a node with an equal key.
3. Not found → "nothing". Found → return a **copy** of the value.

Why a probe? `HMap::lookup` only accepts an `HNode*`. The probe is a
throwaway object that carries the key we're searching for.

### `set` (lines 58–67)

```cpp
    void set(std::string_view key, std::string_view val) {
        Entry probe = makeProbe(key);
        if (HNode *node = map_.lookup(&probe)) {
            static_cast<Entry *>(node)->val = val;
            return;
        }
        auto *entry = new Entry(std::move(probe));
        entry->val = val;
        map_.insert(entry);
    }
```

- If the key exists, overwrite its value in place.
- Otherwise, create a new `Entry` on the heap and insert it.

**Line 64:** `new Entry(std::move(probe))` turns the probe into the real
entry by *moving* it: the key string's memory is transferred (not copied),
and the already-computed `hcode` comes along. So the key is hashed only once.

> **C++ note — `new` / `delete`:** the entry must outlive this function, so
> it goes on the heap. Normally you'd use `std::unique_ptr` for that, but an
> intrusive container stores raw `HNode*`, so ownership is manual: the map
> owns entries while they're inside it; `del` and `~HMap` free them.

> **C++ note — assigning a `string_view` to a `string`:** `entry->val = val;`
> copies the viewed characters into the string. We must copy, because the
> view points into the connection's input buffer, which will be erased soon.

### `del` (lines 69–77)

```cpp
    bool del(std::string_view key) {
        Entry probe = makeProbe(key);
        HNode *node = map_.pop(&probe);
        if (!node) {
            return false;
        }
        entryDelete(node);
        return true;
    }
```

Remove the entry from the map. `pop` hands ownership back to us, so we must
free it. Returns whether the key existed.

### `makeProbe` and the map (lines 79–88)

```cpp
private:
    static Entry makeProbe(std::string_view key) {
        Entry probe;
        probe.key = key;
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(key.data()), key.size());
        return probe;
    }

    HMap map_{entryEq, entryDelete};
};
```

- `makeProbe` copies the key and computes its FNV-1a hash.
- `map_` is constructed with our two callbacks right where it's declared.

> **C++ note — `HMap map_{entryEq, entryDelete};`:** a default member
> initializer using braces. Every `KvStore` builds its `map_` this way, so
> `KvStore` doesn't need to write a constructor. When a `KvStore` is
> destroyed, `map_`'s destructor frees all remaining entries.

A small cost to know about: every `get`/`set`/`del` copies the key into the
probe. A zero-copy design would compare against a `string_view` instead.

---

## Lines 90–106: `runCommand`

```cpp
static void runCommand(KvStore &store, const std::vector<std::string> &args, Buffer &out) {
    if (args.size() == 2 && args[0] == "get") {
        auto val = store.get(args[1]);
        if (val) {
            encodeResponse(out, ResponseStatus::Ok, *val);
        } else {
            encodeResponse(out, ResponseStatus::Nx);
        }
    } else if (args.size() == 3 && args[0] == "set") {
        store.set(args[1], args[2]);
        encodeResponse(out, ResponseStatus::Ok);
    } else if (args.size() == 2 && args[0] == "del") {
        encodeResponse(out, store.del(args[1]) ? ResponseStatus::Ok : ResponseStatus::Nx);
    } else {
        encodeResponse(out, ResponseStatus::Err);
    }
}
```

The command dispatcher. Match on the command name **and** the argument
count, run it, and encode the reply into `out`.

| Input | Reply |
|---|---|
| `get k` (2 args) | `Ok` + value, or `Nx` |
| `set k v` (3 args) | `Ok` |
| `del k` (2 args) | `Ok` if it existed, `Nx` if not |
| anything else (`get` with 3 args, `ping`, …) | `Err` |

Commands are case-sensitive (`GET` gives `Err`). Real Redis is not.

> **C++ note — `*val`:** `val` is `std::optional<std::string>`; `*val` gets
> the string inside it.

---

# Part 2: connections

## Lines 110–122: `Conn`

```cpp
struct Conn {
    explicit Conn(int fd) : fd(fd) { setNonBlocking(fd); }
    ~Conn() { close(fd); }

    Conn(const Conn &) = delete;
    Conn &operator=(const Conn &) = delete;

    const int fd;
    bool wantWrite = false;
    bool wantClose = false;
    Buffer incoming;
    Buffer outgoing;
};
```

Everything the server remembers about one connected client:

| Field | Meaning |
|---|---|
| `fd` | The client's socket |
| `wantWrite` | We have reply bytes waiting to be sent, so ask `poll()` to tell us when the socket is writable |
| `wantClose` | Something went wrong or the client left; close this connection at the end of this loop iteration |
| `incoming` | Bytes received but not yet processed (may hold a partial request) |
| `outgoing` | Reply bytes not yet sent (the socket may not take them all at once) |

**Why keep buffers at all?** Because nothing arrives or leaves in neat
messages. `incoming` holds half a request until the rest arrives; `outgoing`
holds whatever `write()` couldn't send yet. A blocking server gets this
"for free" by sleeping; a non-blocking server must remember where it was.

**RAII:** the constructor makes the socket non-blocking, and the destructor
closes it. Destroying a `Conn` (by resetting its `unique_ptr`) is all it
takes to close a connection and free its buffers.

Copying is forbidden: two `Conn` copies would both `close()` the same fd.
The second close could even close a *different* connection that was given
the same fd number in between.

> **C++ note — `explicit`:** stops the compiler from silently converting an
> `int` into a `Conn`. Without it, `Conn c = 5;` would compile.

> **C++ note — `const int fd`:** the fd never changes after construction.
> `: fd(fd)` initialises the member `fd` from the parameter `fd` (the member
> is outside the parentheses, the parameter inside).

> **CN refresher — one fd per client:** the listening socket only accepts
> new connections. Every accepted client gets its **own** new socket fd, and
> all of that client's data goes through it. So one `Conn` = one fd = one
> client.

---

## Lines 124–146: `handleRequests`, processing every complete request

```cpp
// Handles every complete request in the buffer (clients may pipeline).
static void handleRequests(KvStore &store, Conn &conn) {
    while (true) {
        size_t payloadLen = 0;
        FrameStatus status = tryParseFrame(conn.incoming.data(), conn.incoming.size(), payloadLen);
        if (status == FrameStatus::Incomplete) {
            return;
        }
```

Look at the front of `incoming`. If there isn't a whole frame yet, stop and
wait for more bytes (they'll come on a later `read`).

```cpp
        std::optional<std::vector<std::string>> args;
        if (status == FrameStatus::Complete) {
            args = parseRequest(conn.incoming.data() + kHeaderLen, payloadLen);
        }
        if (!args) {
            conn.wantClose = true;
            return;
        }
```

If the frame is complete, parse its payload (skipping the 4-byte header).
If the frame was `Malformed` (too big), `args` stays empty; if the payload
didn't parse, `parseRequest` returns empty. **Either way: close the
connection.** There's no way to resync with a client that sent garbage,
because we no longer know where the next message starts.

```cpp
        Buffer response;
        runCommand(store, *args, response);
        appendFrame(conn.outgoing, response);
        conn.incoming.consume(kHeaderLen + payloadLen);
    }
}
```

Run the command, frame the reply and queue it in `outgoing`, then drop the
processed request from the front of `incoming`. Loop to see whether another
complete request is already waiting.

> **CN refresher — pipelining:** a client may send several requests without
> waiting for replies. **Example:** the client sends `set a 1`, `set b 2`,
> `get a` back-to-back. One `read()` might return all three (TCP merged
> them). This loop handles all three in order and queues three replies. TCP
> guarantees ordering, so the client receives replies in the same order it
> sent the requests. See [01 §15](01-networking-refresher.md#15-latency-throughput-and-pipelining).

---

## Lines 148–161: `handleRead`

```cpp
static void handleRead(KvStore &store, Conn &conn) {
    uint8_t buf[64 * 1024];
    ssize_t rv = read(conn.fd, buf, sizeof(buf));
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv <= 0) {
        conn.wantClose = true;
        return;
    }
    conn.incoming.append(buf, static_cast<size_t>(rv));
    handleRequests(store, conn);
    conn.wantWrite = conn.outgoing.size() > 0;
}
```

Called when `poll()` says this socket is readable.

1. **Line 149:** a 64 KB scratch array on the stack (no heap allocation).
2. **Line 150:** read whatever has arrived, up to 64 KB. On a non-blocking
   socket this never sleeps.
3. **Lines 151–153:** `EAGAIN`: nothing there after all. Not an error; just
   return. (Rare right after `poll` said "readable", but possible.)
4. **Lines 154–157:**
   - `rv == 0` → **EOF**: the client closed its side of the connection.
   - `rv < 0` with another errno → real error (e.g. `ECONNRESET`).
   - Both mean: close this connection.
5. **Line 158:** append the new bytes to `incoming`.
6. **Line 159:** process every complete request now in the buffer.
7. **Line 160:** if any replies are queued, ask `poll()` to tell us when we can write.

**Only one `read` per loop:** if a client sent more than 64 KB, the rest
stays in the kernel's buffer. Since `poll()` is level-triggered, it reports
this socket as readable again on the next loop. This also keeps one busy
client from hogging the loop.

> **CN refresher — `read()` return values on a socket:**
>
> | `rv` | Meaning |
> |---|---|
> | `> 0` | Got `rv` bytes |
> | `0` | EOF: the peer closed its sending side (sent a TCP FIN) |
> | `-1`, errno `EAGAIN` | Non-blocking: nothing available right now |
> | `-1`, other errno | Error, e.g. `ECONNRESET` (peer crashed / reset) |

---

## Lines 163–174: `handleWrite`

```cpp
static void handleWrite(Conn &conn) {
    ssize_t rv = write(conn.fd, conn.outgoing.data(), conn.outgoing.size());
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv < 0) {
        conn.wantClose = true;
        return;
    }
    conn.outgoing.consume(static_cast<size_t>(rv));
    conn.wantWrite = conn.outgoing.size() > 0;
}
```

Called when `poll()` says the socket is writable.

1. Try to write everything in `outgoing`.
2. `EAGAIN`: the kernel's send buffer is full; try again next time.
3. Other error (e.g. `EPIPE`: the client is gone): close.
4. Remove the bytes that **were** written from `outgoing`. If `write`
   only accepted part, the rest stays for the next loop.
5. Keep asking for `POLLOUT` only while something is left.

> **CN refresher — why `write` can be partial:** `write()` copies bytes
> into the kernel's per-socket **send buffer** (typically tens to hundreds
> of KB). If a client stops reading, its receive buffer fills, TCP tells our
> side to stop sending, our send buffer fills, and `write()` can only accept
> part (or nothing: `EAGAIN`). A blocking server would freeze here; ours
> just keeps the rest in `outgoing` and moves on to other clients.

---

## Lines 176–196: `makeListener`

```cpp
static int makeListener() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        die("socket()");
    }
```

Create a TCP (`SOCK_STREAM`) IPv4 (`AF_INET`) socket.

```cpp
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
```

> **CN refresher — `SO_REUSEADDR`:** when a TCP connection closes, the side
> that closed first keeps its address in a **TIME_WAIT** state for 30–60
> seconds, to catch stray late packets. If you stop the server and start it
> again right away, `bind()` would fail with `Address already in use` until
> TIME_WAIT ends. `SO_REUSEADDR` lets you bind anyway. Every server sets it.
> See [01 §5](01-networking-refresher.md#closing-fin-and-time_wait).

```cpp
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(kServerPort);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(fd, reinterpret_cast<sockaddr *>(&addr), sizeof(addr)) != 0) {
        die("bind()");
    }
```

**`bind`** attaches the socket to a local address: IP `127.0.0.1`, port
`1234`. `htons`/`htonl` convert to network byte order (big-endian), which
the socket API requires.

> **CN refresher — binding to 127.0.0.1 vs 0.0.0.0:** `127.0.0.1` (loopback)
> means only programs on this machine can connect. `0.0.0.0`
> (`INADDR_ANY`) would accept connections from the network too. For a
> database with no password, loopback-only is the safe choice.

```cpp
    if (listen(fd, SOMAXCONN) != 0) {
        die("listen()");
    }
    setNonBlocking(fd);
    return fd;
}
```

**`listen`** turns the socket into a *listening* socket: the kernel will now
complete TCP handshakes with clients on its own and queue the finished
connections (the **backlog**) until we `accept()` them. `SOMAXCONN` asks for
the system's maximum queue length (128 on macOS).

The listening socket is non-blocking too, so `accept()` can never freeze the
loop (for example, if a client connects and immediately disconnects between
`poll` and `accept`).

> **CN refresher — the server socket sequence:**
> `socket → setsockopt → bind → listen → (loop) accept`. Client side:
> `socket → connect`. See [01 §7](01-networking-refresher.md#7-sockets-and-file-descriptors).

---

# Part 3: the event loop

## Lines 200–207: setup

```cpp
int main() {
    signal(SIGPIPE, SIG_IGN);
    KvStore store;
    int listenFd = makeListener();
    fprintf(stderr, "listening on 127.0.0.1:%d\n", kServerPort);

    std::vector<std::unique_ptr<Conn>> conns;  // indexed by fd
    std::vector<pollfd> pollArgs;
```

- **Line 201: ignore `SIGPIPE`.**

  > **CN refresher — SIGPIPE:** if you `write()` to a socket whose peer has
  > already closed, the OS sends your process the `SIGPIPE` signal, and its
  > default action is to **kill the process**. So any client that disconnects
  > at the wrong moment could crash the whole server. Ignoring the signal
  > makes `write()` return `-1` with `errno = EPIPE` instead, which
  > `handleWrite` handles by closing just that connection.

- **Line 202:** the one and only data store, for all clients.
- **Line 206: `conns`** maps fd → connection. Slot `fd` holds that client's
  `Conn`, or `nullptr` if that fd isn't a client.

  Why a vector indexed by fd instead of a `std::unordered_map<int, Conn>`?
  The OS always gives out the **lowest unused fd number**, so fds are small
  and dense (4, 5, 6, …). A vector lookup is a single array access.

- **Line 207: `pollArgs`**, the array we pass to `poll()`. Declared outside
  the loop so its memory is reused each iteration.

> **C++ note — `std::unique_ptr<Conn>`:** a smart pointer that owns one heap
> object and deletes it automatically. `conns[fd].reset()` deletes the
> `Conn`, which runs `~Conn()`, which closes the socket. No manual `delete`
> anywhere.

---

## Lines 209–217: build the poll list

```cpp
    while (true) {
        pollArgs.clear();
        pollArgs.push_back({listenFd, POLLIN, 0});
        for (const auto &conn : conns) {
            if (conn) {
                short events = POLLIN | (conn->wantWrite ? POLLOUT : 0);
                pollArgs.push_back({conn->fd, events, 0});
            }
        }
```

Each loop iteration starts by telling `poll()` what we care about:
- **Slot 0** is always the listening socket, watching `POLLIN` (for a
  listening socket, "readable" means "a new connection is waiting").
- Then one entry per connected client:
  - always `POLLIN` ("tell me when this client sends something or disconnects"),
  - plus `POLLOUT` only if we have replies waiting to be sent.

> **CN refresher — why not always ask for POLLOUT?** A socket is writable
> almost all the time (its send buffer usually has room). If we always
> asked, `poll()` would return immediately every time and the loop would spin
> at 100% CPU doing nothing. So we only ask when `outgoing` is non-empty.

> **C++ note — `{listenFd, POLLIN, 0}`:** brace-initialises a `pollfd`
> struct: `fd`, `events`, `revents`. `revents` is where the kernel writes
> its answer.

Note: `POLLIN` is requested even when the client has a huge backlog of
unsent replies. That's the "no backpressure" limitation.

---

## Lines 219–224: wait

```cpp
        if (poll(pollArgs.data(), static_cast<nfds_t>(pollArgs.size()), -1) < 0) {
            if (errno == EINTR) {
                continue;
            }
            die("poll()");
        }
```

**This is the only place the server ever sleeps.** `poll()` blocks until at
least one of the listed sockets is ready (timeout `-1` = wait forever), then
fills in each entry's `revents`.

- `EINTR`: a signal (e.g. from a debugger) interrupted the wait. Harmless;
  loop and try again.
- Any other failure is unexpected: exit.

> **CN refresher — what `poll()` does:** you give the kernel a list of fds
> and what you're interested in; it puts your thread to sleep until at least
> one is ready, then tells you which. One thread can wait on thousands of
> sockets at once. This is **I/O multiplexing**.
>
> `poll()` checks **every** fd you pass, every call: O(number of
> connections). Linux's **epoll** and macOS's **kqueue** instead remember
> your fds in the kernel and only return the ready ones: O(ready
> connections). At 200 clients the difference is tiny; at 50,000 mostly-idle
> clients it's huge. See [01 §10](01-networking-refresher.md#10-serving-many-clients-io-multiplexing).

---

## Lines 226–234: accept a new client

```cpp
        if (pollArgs[0].revents & POLLIN) {
            int fd = accept(listenFd, nullptr, nullptr);
            if (fd >= 0) {
                if (static_cast<size_t>(fd) >= conns.size()) {
                    conns.resize(static_cast<size_t>(fd) + 1);
                }
                conns[static_cast<size_t>(fd)] = std::make_unique<Conn>(fd);
            }
        }
```

If the listening socket is readable, a finished connection is waiting in the
backlog.

- `accept()` takes it off the queue and returns a **new fd** for that client.
  The two `nullptr`s mean "I don't need the client's address".
- Grow `conns` if this fd is beyond the end, then store a new `Conn` in its
  slot. The `Conn` constructor makes the socket non-blocking.
- If `accept` fails (e.g. the client already gave up), just skip it.

Only **one** connection is accepted per loop. If 50 clients connect at once,
the rest stay in the backlog; `poll()` is level-triggered, so it reports
the listener as ready again next time, and we accept one per iteration. A
faster design would loop `accept()` until `EAGAIN`.

The new client isn't in this iteration's `pollArgs`, so it's first polled on
the next iteration.

> **C++ note — `std::make_unique<Conn>(fd)`:** creates a `Conn` on the heap
> and wraps it in a `unique_ptr`. Assigning into `conns[fd]` would delete
> any previous `Conn` in that slot (there never is one, because a slot is
> cleared when its fd is closed).

> **C++ note — `revents & POLLIN`:** `revents` is a bit mask; `&` with a flag
> checks whether that bit is set.

---

## Lines 236–251: serve ready clients

```cpp
        for (size_t i = 1; i < pollArgs.size(); i++) {
            short revents = pollArgs[i].revents;
            auto &conn = conns[static_cast<size_t>(pollArgs[i].fd)];
            if (!revents || !conn) {
                continue;
            }
```

Go through every client entry (index 0 was the listener). Skip it if
nothing happened to it. `conn` is a **reference** to the `unique_ptr` slot,
so resetting it below clears the slot in `conns` itself.

(`!conn` is a defensive check; each fd appears at most once in `pollArgs`,
so a slot can't be emptied before we reach it.)

```cpp
            if (revents & POLLIN) {
                handleRead(store, *conn);
            }
            if (!conn->wantClose && (revents & POLLOUT)) {
                handleWrite(*conn);
            }
            if (conn->wantClose || (revents & (POLLERR | POLLHUP))) {
                conn.reset();
            }
        }
    }
}
```

1. **Readable** → read and process requests (this may queue replies).
2. **Writable**, and not already marked for closing → send queued replies.
3. **Close** if we marked it, or the kernel reported an error (`POLLERR`) or
   hang-up (`POLLHUP`). `reset()` destroys the `Conn`: its destructor closes
   the socket and its buffers are freed. The fd number becomes free for the
   OS to reuse.

`POLLERR` and `POLLHUP` are always reported by `poll()`, even though we
never asked for them.

The `while (true)` loop never ends; the server runs until it's killed.

---

## One request, start to finish

Follow `build/client get foo` through the server:

```
iteration 1
  poll: listener POLLIN                  -> accept(): fd 5, conns[5] = new Conn
iteration 2
  pollArgs has {5, POLLIN}
  poll: fd 5 POLLIN (client sent 22 bytes: 4 header + 18 payload)
  handleRead: read 22 bytes -> incoming
    handleRequests: tryParseFrame -> Complete, payloadLen 18
      parseRequest -> {"get", "foo"}
      runCommand -> store.get("foo") -> "bar" -> response 00 03000000 626172
      appendFrame -> outgoing = 08000000 00 03000000 626172 (12 bytes)
      consume 22 bytes; incoming empty -> Incomplete -> return
    wantWrite = true
iteration 3
  pollArgs has {5, POLLIN|POLLOUT}
  poll: fd 5 POLLOUT
  handleWrite: write 12 bytes; outgoing empty; wantWrite = false
iteration 4
  poll: fd 5 POLLIN (client closed its socket)
  handleRead: read() returns 0 -> wantClose -> conns[5].reset() -> close(5)
```

Notice the reply is sent one iteration **after** the request is processed:
`handleRead` sets `wantWrite`, but this iteration's `poll()` wasn't asked
about `POLLOUT`, so the write waits for the next `poll()`. An optimisation
(used in later chapters of the book) is to try `write()` immediately after
processing, since the socket is almost always writable.

## Connection state at a glance

```
            accept()
               │
               ▼
   ┌──── waiting for data ◄──────────────┐
   │     (POLLIN only)                    │ outgoing drained
   │           │ read, replies queued     │
   │           ▼                          │
   │     has replies to send ─────────────┘
   │     (POLLIN + POLLOUT)
   │           │
   │  EOF / error / malformed request / POLLERR / POLLHUP
   ▼           ▼
       closed (Conn destroyed, fd closed)
```
