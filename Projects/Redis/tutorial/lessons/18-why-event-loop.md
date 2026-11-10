---
title: One slow client freezes everyone (why we need an event loop)
module: The event-loop server
time: 45 min
---

:::goal
See with your own eyes why a simple "accept → read → reply" server can't
serve two clients at once. Then learn the three ideas behind how Redis, NGINX
and Node.js serve thousands of clients **with a single thread**: non-blocking
sockets, readiness notification with `poll()`, and per-connection buffers.
:::

## The experiment: a lazy client blocks a busy one

:::task Freeze the hello server
1. Terminal 1: start `build/hello_server` from Part 3.
2. Terminal 2: run `nc 127.0.0.1 1234` but **don't type anything**.
3. Terminal 3 (open a third one): run `build/hello_client`.
:::

```output
Terminal 3 just hangs. No "server says: world".
Now type anything + Enter in terminal 2, and terminal 3 instantly completes.
```

Why? The server accepted the `nc` connection and called `read()` on it.
**`read()` waits ("blocks") until that client sends something.** While it
waits, the server can't do anything else: it can't accept, can't read from
anyone else, can't reply. One idle client froze the whole server.

:::analogy
A waiter takes your order, then **stands at your table staring at you** until
you decide. Every other table waits. That's a blocking server. A good waiter
says "I'll come back when you're ready" and serves other tables meanwhile.
That's an event loop.
:::

## Option 1: one thread per client

We could start a new **thread** for every client, so each one can block
without hurting the others. That works, and it's simple. But:

- each thread needs its own stack memory (often 512 KB – 8 MB)
- switching between thousands of threads costs CPU time
- threads sharing one hashtable need **locks**, a whole new class of bugs

Real Redis instead uses **one thread** with an **event loop**, and so will we.

## Option 2: the event loop

The idea: **never call anything that might wait**, except for one special
function that waits for *all* sockets at once.

```text
loop forever:
    1. ask the kernel: "which of my sockets are ready?"   ← the ONLY place we wait
    2. for each ready socket:
         listening socket ready → accept() the new client
         client readable        → read() what's there (won't block, data is waiting)
         client writable        → write() what we have queued (won't block, there's room)
```

Three tools make this work.

### Tool 1: non-blocking sockets

A socket can be switched to **non-blocking mode** (flag `O_NONBLOCK`). Then
`read`/`write`/`accept` **never wait**. If they can't make progress right
now, they return `-1` immediately with `errno == EAGAIN` ("try again later").
(You may also see the name `EWOULDBLOCK`. On Linux and macOS it's the same
number, so checking `EAGAIN` is enough.)

| Situation | Blocking socket | Non-blocking socket |
|---|---|---|
| `read`, data waiting | returns data | returns data |
| `read`, no data yet | **waits** | returns -1, `errno = EAGAIN` |
| `write`, room in send buffer | copies, returns | copies, returns |
| `write`, send buffer full | **waits** | returns -1, `errno = EAGAIN` (or writes part) |
| `accept`, client waiting | returns new fd | returns new fd |
| `accept`, nobody waiting | **waits** | returns -1, `errno = EAGAIN` |

### Tool 2: readiness notification with `poll()`

Non-blocking calls alone would make us spin in a loop asking "ready yet? ready
yet?", burning 100% CPU. Instead we give the kernel a **list of fds** and
what we care about, and `poll()` sleeps until at least one is ready:

```cpp
struct pollfd {
    int   fd;       // which socket (you fill in)
    short events;   // what you want to know about (you fill in)
    short revents;  // what actually happened (the kernel fills in)
};
poll(fds.data(), fds.size(), -1);   // array of pollfd, how many, timeout (-1 = wait forever)
```

| Flag | In `events` means | In `revents` means |
|---|---|---|
| `POLLIN` | tell me when I can read | data arrived, **or** the peer closed (read will return 0). On a listening socket: a client is waiting to be accepted. |
| `POLLOUT` | tell me when I can write | there's room in the send buffer |
| `POLLERR` | (always reported) | the socket has an error |
| `POLLHUP` | (always reported) | the connection was hung up |

The flags are **bits**, combined with `|` and tested with `&`:

```cpp
short events = POLLIN | POLLOUT;      // want both
if (revents & POLLIN) { /* readable */ }
```

:::net `poll`, `epoll`, `kqueue`, `select`
All of these do the same job. `select` is the oldest and limited to 1024
fds. `poll` works everywhere (macOS + Linux) and is the simplest, so we use
it. `epoll` (Linux) and `kqueue` (macOS/BSD) scale better to tens of
thousands of connections, because they don't re-send the whole list on every
call. Swapping them in later is a great exercise.
:::

### Tool 3: per-connection buffers

With non-blocking reads, a request may arrive in pieces over several loop
iterations. So each client needs **its own state that survives between
iterations**:

```text
struct Conn {
    fd                 which socket
    incoming buffer    bytes received but not processed yet (maybe half a request)
    outgoing buffer    replies generated but not sent yet
    wantWrite          do we have something to send? (ask poll for POLLOUT)
    wantClose          should the loop destroy this connection?
}
```

The flow for one client becomes:

```text
POLLIN  → read whatever arrived → append to incoming
        → while incoming has a complete frame:
              parse request → run command → append framed reply to outgoing
              erase that frame from incoming
        → if outgoing is non-empty: wantWrite = true
POLLOUT → write as much of outgoing as the socket accepts → erase what was written
        → if outgoing is empty: wantWrite = false
```

This is exactly what you'll build over the next four lessons:

| Lesson | Server stage |
|---|---|
| 5.2 | Non-blocking listener + `poll()` loop that accepts |
| 5.3 | `Conn` objects: read into `incoming`, close on EOF |
| 5.4 | Parse frames, queue replies, write them out + the real client |
| 5.5 | Real `get`/`set`/`del` commands |

:::quiz Why does the event-loop server never need locks?
There's only **one thread**. Only one piece of code runs at any moment, so
two requests can never modify the hashtable at the same time. Requests are
handled one after another, very quickly.
:::

:::quiz When would a single-threaded event loop be a bad idea?
When handling a request takes a long time **on the CPU**, like compressing
a large file. While the loop is busy computing, every other client waits.
Redis is fine because `get`/`set` take microseconds. Slow work is the
reason the book's later chapters add a thread pool.
:::

:::quiz Why would asking for `POLLOUT` all the time be a bug?
A socket's send buffer almost always has room, so `poll()` would report
"writable!" instantly on every call. The loop would spin at 100% CPU doing
nothing. Ask for `POLLOUT` **only when you have bytes waiting to be sent**.
:::

:::recap
- A blocking server waits on one client and ignores the rest.
- Event loop = **non-blocking sockets** + **`poll()`** to wait for any ready socket + **per-connection buffers**.
- `EAGAIN` = "not ready, try later". It's not a real error.
- `POLLIN`/`POLLOUT`/`POLLERR`/`POLLHUP` are bit flags: combine with `|`, test with `&`.
:::
