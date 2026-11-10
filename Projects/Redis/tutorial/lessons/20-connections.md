---
title: Keeping track of many connections
module: The event-loop server
time: 40 min
---

:::goal
Give every client a **`Conn`** struct that remembers its socket and buffers,
store all connections in a vector **indexed by fd**, poll all of them, read
from whichever are ready, and close the ones that hang up. At the end of this
lesson your server serves **several `nc` sessions at the same time**.
:::

## The `Conn` struct (final version)

```cpp
struct Conn {
    int fd = -1;
    bool wantWrite = false;  // outgoing has bytes: ask poll() for POLLOUT
    bool wantClose = false;  // the event loop should close this connection
    string incoming;         // bytes read but not handled yet
    string outgoing;         // replies waiting to be written
};
```

That's all the state one client needs between loop iterations. `incoming` and
`outgoing` are the byte buffers from Part 4, plain strings.

## Mapping fd → Conn: a vector, not a hashmap

When `poll()` says "fd 7 is readable", we must find fd 7's `Conn` quickly.
Since the kernel always hands out the **lowest free** fd numbers, fds are
small and close together (3, 4, 5, …). So a plain vector indexed by fd is
perfect:

```cpp
vector<Conn *> conns;  // conns[fd] is the connection on that fd, or nullptr
```

```text
index:   0      1      2      3        4        5        6
conns: [null] [null] [null] [null]  [Conn*]  [null]  [Conn*]
                            listener  client           client
```

- `conns[fd]` is O(1) and needs no hashing.
- `nullptr` means "no client on this fd".

## Accepting into the vector

```cpp
int fd = accept(listenFd, nullptr, nullptr);
if (fd >= 0) {
    setNonBlocking(fd);
    if (fd >= (int)conns.size()) conns.resize(fd + 1, nullptr);  // grow so conns[fd] exists
    conns[fd] = new Conn();
    conns[fd]->fd = fd;
}
```

`resize` fills the new slots with `nullptr`. The `(int)` is there because
`size()` is unsigned and `fd` is an `int`, and the compiler warns when you
compare the two.

## Polling every connection

Building the list now adds one entry per live connection:

```cpp
vector<pollfd> fds;
fds.push_back({listenFd, POLLIN, 0});      // always slot 0
for (Conn *conn : conns) {
    if (conn == nullptr) continue;          // skip empty slots
    fds.push_back({conn->fd, POLLIN, 0});
}
```

After `poll()` returns, handle the listener (slot 0) as before, then walk the
rest:

```cpp
for (size_t i = 1; i < fds.size(); i++) {
    short ready = fds[i].revents;
    if (ready == 0) continue;                // nothing happened on this one
    Conn *conn = conns[fds[i].fd];
    if (ready & POLLIN) handleRead(conn);
    if (conn->wantClose || (ready & (POLLERR | POLLHUP))) {
        close(conn->fd);                     // hang up
        conns[conn->fd] = nullptr;           // free the slot
        delete conn;                         // free the memory
    }
}
```

Closing a connection is three steps: close the socket, empty its slot in
`conns`, and `delete` the `Conn` we made with `new`.

## Reading (version 1)

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
    cout << "fd " << conn->fd << ": read " << n << " bytes, "
         << conn->incoming.size() << " bytes buffered so far" << endl;
}
```

- One `read` of up to 64 KB per wake-up. If more is waiting, `poll` will
  report `POLLIN` again next time around. (`POLLIN` stays on as long as
  there's unread data.)
- `0` = EOF and `-1` (other than `EAGAIN`) = real error. Both mean "close it".
  We set the flag and let the **loop** do the closing.
- `incoming.append(buf, n)` adds exactly the `n` bytes we got. Nothing is
  lost between reads.

:::why Why set `wantClose` instead of closing right here?
Separation of jobs. `handleRead` handles data. The event loop owns the
connections. If `handleRead` deleted its own `Conn`, the loop would be left
holding a pointer to freed memory. The loop checks the flag right after and
cleans up safely.
:::

:::task Serve many `nc` clients at once
Update `src/server.cpp`:

1. Add the `Conn` struct and `handleRead` (version 1, with the `cout`).
2. In `main`, create `conns`, add every live connection to `fds`, store
   accepted fds in `conns` (print `fd N: connected`), and add the loop over
   ready connections. Before closing, print `fd N: closed`.

```bash
$ c++ -std=c++17 -Wall src/server.cpp src/protocol.cpp -o build/server
$ build/server
```

Open **two** more terminals and run `nc 127.0.0.1 1234` in each. Type
`hello` in the first and `hi` in the second (press Enter after each), then
quit both with Ctrl + C.
:::

```output
listening on 127.0.0.1:1234
fd 4: connected
fd 5: connected
fd 4: read 6 bytes, 6 bytes buffered so far
fd 5: read 3 bytes, 3 bytes buffered so far
fd 4: closed
fd 5: closed
```

(The exact order depends on what you do first.) **Both clients are served
at the same time, by one thread.** Compare that with the frozen hello server!
The `nc` clients don't get any reply yet. That's next lesson.

:::solution
@include code/e-server/s2/src/server.cpp
:::

:::quiz Type a long line into `nc` and press Enter. Then another. Why does "bytes buffered so far" keep growing?
We append everything to `incoming` but never remove anything, because we
don't handle requests yet. Next lesson, complete frames get erased from the
front of `incoming`.
:::

:::recap
- `Conn` = socket fd + `incoming`/`outgoing` strings + two flags.
- `vector<Conn *> conns` indexed by fd: O(1) lookup, `nullptr` = free slot.
- Each loop: poll listener + every live connection → accept / `handleRead` → close on `wantClose`, `POLLERR` or `POLLHUP`.
- Closing = `close(fd)`, `conns[fd] = nullptr`, `delete conn`.
:::
