---
title: A non-blocking listener and the poll() loop
module: The event-loop server
time: 35 min
---

:::goal
Start `src/server.cpp`, the real server. Write `setNonBlocking()` and the
final `makeListener()`, then the skeleton of the event loop: build the
`pollfd` list, call `poll()`, and accept connections when the listener is
ready.
:::

## `setNonBlocking()`: flipping one bit with `fcntl`

Every fd has a set of **status flags** stored as bits in an `int`.
`O_NONBLOCK` is one of those bits. To turn it on without disturbing the
others, we **read** the flags, **OR** in our bit, and **write** them back:

```cpp
// After this, read/write/accept on fd never wait. If they can't do anything
// right now they return -1 with errno == EAGAIN.
void setNonBlocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);       // read
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);  // add our bit, write back
}
```

```text
flags (example):       0000 0010   (some existing flag)
O_NONBLOCK:            0000 0100
flags | O_NONBLOCK:    0000 0110   ← old flag kept, new flag added
```

:::why Why `|` and not just `fcntl(fd, F_SETFL, O_NONBLOCK)`?
That would **overwrite** all the flags with only `O_NONBLOCK`, wiping out
any others the fd had. Read–modify–write is the safe pattern whenever you
change one bit.
:::

## The final `makeListener()`

Same as Part 3, with two changes: the port comes from `PORT` in
`protocol.h`, and the listening socket is made non-blocking:

```cpp
int makeListener() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) die("socket()");
    int yes = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));  // allow quick restarts

    sockaddr_in addr = {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);  // 127.0.0.1
    if (::bind(fd, (sockaddr *)&addr, sizeof(addr)) != 0) die("bind()");
    if (listen(fd, SOMAXCONN) != 0) die("listen()");
    setNonBlocking(fd);
    return fd;
}
```

:::why Why make the *listening* socket non-blocking, if poll says it's ready?
Because "ready" can go stale. Between `poll()` saying "a client is waiting"
and our `accept()`, that client might give up and disconnect. A **blocking**
`accept()` would then wait for the *next* client, freezing the whole server.
A non-blocking one just returns `-1` and the loop moves on.
:::

## The loop skeleton

```cpp
int main() {
    int listenFd = makeListener();
    cout << "listening on 127.0.0.1:" << PORT << endl;

    while (true) {
        vector<pollfd> fds;
        fds.push_back({listenFd, POLLIN, 0});

        if (poll(fds.data(), fds.size(), -1) < 0) {
            if (errno == EINTR) continue;  // interrupted by a signal, just retry
            die("poll()");
        }

        if (fds[0].revents & POLLIN) {
            int fd = accept(listenFd, nullptr, nullptr);
            if (fd >= 0) {
                cout << "accepted a connection on fd " << fd << endl;
                close(fd);
            }
        }
    }
}
```

Line by line:

- `fds` is rebuilt **every time around the loop**, because the set of clients
  and what we want from each changes over time. For now it only holds the
  listener, asking for `POLLIN` ("tell me when a client is waiting").
- `{listenFd, POLLIN, 0}` fills in a `pollfd`'s three fields in order:
  `fd`, `events`, `revents`.
- `poll(array, count, -1)` sleeps until something is ready. `fds.data()` is
  the address of the vector's first element, which is what `poll` wants.
- `fds[0].revents & POLLIN` tests whether the kernel set the `POLLIN` bit for
  the listener.

:::why What is `EINTR` and why `continue`?
If the process receives a **signal** (an OS notification, e.g. when you
resize the terminal) while sleeping in `poll()`, the call returns early with
`errno == EINTR` ("interrupted"). That's not an error, so just loop again.
:::

:::task Write the first version of `src/server.cpp`
1. Includes: `<cerrno>`, `<cstdlib>`, `<cstring>`, `<iostream>`, `<string>`,
   `<vector>`, then `<arpa/inet.h>`, `<fcntl.h>`, `<poll.h>`, `<unistd.h>`,
   then `"protocol.h"` and `using namespace std;`.
2. `die()` (same as before), `setNonBlocking()`, `makeListener()`, `main()` as above.
3. Build. The server needs `protocol.cpp` linked in too:

```bash
$ c++ -std=c++17 -Wall src/server.cpp src/protocol.cpp -o build/server
$ build/server
```

4. In terminal 2:

```bash
$ nc -z 127.0.0.1 1234
$ nc -z 127.0.0.1 1234
```
:::

```output
listening on 127.0.0.1:1234
accepted a connection on fd 4
accepted a connection on fd 4
```

It looks just like Part 3's listener from the outside, but now the program
only ever waits in `poll()`. Stop it with Ctrl + C.

:::hint Hint: "unknown type name 'pollfd'"
Make sure you included `<poll.h>`. `pollfd`, `POLLIN` and `poll` come from
there.
:::

:::solution
@include code/e-server/s1/src/server.cpp
:::

:::recap
- `setNonBlocking`: read flags with `F_GETFL`, `| O_NONBLOCK`, write with `F_SETFL`.
- The listener is non-blocking too, so a stale "ready" can't freeze us.
- Each loop: rebuild `fds` → `poll()` (retry on `EINTR`) → act on `revents`.
:::
