---
title: Your own client with connect()
module: First server & client
time: 25 min
---

:::goal
Replace `nc` with your own client program. The client side of the socket API
is short: `socket()` then `connect()`. After that it's `write`/`read` like
before.
:::

## The client recipe

```text
socket()   → blank socket
connect()  → do the TCP handshake with 127.0.0.1:1234
write()    → send the request
read()     → receive the reply
close()    → hang up
```

`connect()` takes the same `sockaddr_in` we filled in for `bind()`, but here
it means **"the address to call"** rather than "my own address":

```cpp
if (connect(fd, (sockaddr *)&addr, sizeof(addr)) != 0) die("connect()");
```

:::net Which port does the client use?
We never `bind()` the client socket, so the kernel automatically picks a
random free **ephemeral port** (like 52311) during `connect()`. The server
sees the connection as coming from `127.0.0.1:52311`.
:::

:::why What if the server isn't running?
`connect()` fails immediately and `errno` becomes `ECONNREFUSED`. Our `die`
prints `connect() failed: Connection refused`. You'll see this message whenever you
forget to start the server first.
:::

:::task Write the client
Write `scratch/hello_client.cpp`:

1. `die()` as before.
2. `socket(AF_INET, SOCK_STREAM, 0)`.
3. Fill a `sockaddr_in` for `127.0.0.1:1234` and `connect()`.
4. `write` the 5 bytes `hello`.
5. `read` up to 64 bytes into a `char buf[64]` and print
   `server says: <reply>` using `string(buf, n)`.
6. `close` the socket.

With `hello_server` still running in terminal 1, in terminal 2:

```bash
$ c++ -std=c++17 -Wall scratch/hello_client.cpp -o build/hello_client
$ build/hello_client
```
:::

```output
Terminal 2 (client):
server says: world

Terminal 1 (server):
client says: hello
```

Now stop the server (Ctrl + C) and run the client again. You should see
`connect() failed: Connection refused`.

:::hint Hint: the address
It's identical to the server's `bind` code:
```cpp
sockaddr_in addr = {};
addr.sin_family = AF_INET;
addr.sin_port = htons(1234);
addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
```
:::

:::solution
@include code/c-sockets/hello_client.cpp title=scratch/hello_client.cpp
:::

:::cpp Looking ahead: `connectToServer()`
In Part 4 we'll move these client steps into a reusable function in
`protocol.cpp`:

```cpp
int connectToServer();  // returns the connected fd, or -1 on failure
```

The client and the load-tester will both call it. It's the same code you just
wrote, plus one extra option (`TCP_NODELAY`) that we'll explain there.
:::

:::recap
- Client = `socket → connect → write/read → close`. No `bind`/`listen`.
- The client's port is chosen automatically by the kernel.
- `Connection refused` = nothing listening on that port.
:::
