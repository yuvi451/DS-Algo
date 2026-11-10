---
title: TCP is a byte stream: watch it break
module: First server & client
time: 35 min
---

:::goal
Prove to yourself, with a real experiment, that **TCP does not keep message
boundaries**. Two `write()`s can arrive as one `read()`, and one `write()` can
arrive in pieces. Then learn the standard fix, **framing with a length
prefix**, which shapes all of Part 4.
:::

## The experiment

Our client will send `hello` and `world` using **two separate** `write()`
calls. The server will wait one second before its `read()`, so both pieces
have arrived by then. What will the server print?

:::task Run the experiment
1. Copy `scratch/hello_server.cpp` to `scratch/sleepy_server.cpp`. In
   `talk()`, add `sleep(1);` as the **first line** (from `<unistd.h>`, which
   you already include).
2. Copy `scratch/hello_client.cpp` to `scratch/stream_client.cpp`. Replace the
   single `write` with **two** writes:

```cpp
write(fd, "hello", 5);
write(fd, "world", 5);
```

3. Build and run both (stop any other server on port 1234 first):

```bash
$ c++ -std=c++17 -Wall scratch/sleepy_server.cpp -o build/sleepy_server
$ c++ -std=c++17 -Wall scratch/stream_client.cpp -o build/stream_client
$ build/sleepy_server          # terminal 1
$ build/stream_client          # terminal 2
```
:::

```output
Terminal 1 (server):
listening on 127.0.0.1:1234
client says: helloworld

Terminal 2 (client):
server says: world
```

**One `read()` returned both writes glued together.** The server has no idea
that the client "meant" two separate messages.

:::solution Show the two files
@include code/c-sockets/sleepy_server.cpp title=scratch/sleepy_server.cpp
@include code/c-sockets/stream_client.cpp title=scratch/stream_client.cpp
:::

## Why this happens

Every TCP socket has two buffers **inside the kernel**:

```text
   your program                 kernel                          network
   write(fd, …) ──copy──► [ send buffer ]    ──TCP sends──►
   read(fd, …)  ◄──copy── [ receive buffer ] ◄──TCP receives──
```

- `write()` **doesn't send anything over the network** by itself. It copies
  your bytes into the kernel's send buffer and returns. The kernel sends them
  whenever it likes, possibly merged with other writes.
- `read()` copies **whatever happens to be** in the receive buffer right now:
  part of a message, exactly one, or several glued together.

:::analogy
TCP is like **water through a pipe**, not letters through the post. You
poured in two cups ("hello", "world"), but the other end just sees water. If
you need to know where one cup ends, you have to mark it yourself.
:::

All of these are possible for the same two writes:

```text
read → "helloworld"              (merged)
read → "hel", read → "loworld"   (split in odd places)
read → "hello", read → "world"   (looks right, but only by luck!)
```

The last case is the dangerous one. Your code works in testing, then breaks
under load. The reverse also happens: a big `write()` of 1 MB may need many
`read()`s on the other side, and `write()` itself may accept only part of
your data if the send buffer is full.

## The fix: framing

The receiver needs a rule for where each message ends. Common options:

| Method | How | Who uses it |
|---|---|---|
| Delimiter | End each message with a special character, e.g. `\n` | HTTP headers, real Redis (RESP) |
| **Length prefix** | Send the message's length first, then the message | **Our project**, many binary protocols |

A delimiter has a problem: what if the message itself contains `\n`? You'd
need escaping rules. A **length prefix** has no such problem. We'll use a
**4-byte length** in front of every message. That's called a **frame**:

```text
┌──────────────┬───────────────────────┐
│ length (4 B) │ payload (length bytes)│
└──────────────┴───────────────────────┘
   05 00 00 00   h  e  l  l  o
```

The receiver's logic becomes completely reliable:

1. Wait until it has **at least 4 bytes**. Read the length `L`.
2. Wait until it has **at least 4 + L bytes**. That's one complete message.
3. Remove those bytes and repeat. Anything left over belongs to the **next**
   message.

:::why Why "wait until it has"? Can't I just call `read(fd, buf, L)`?
`read(fd, buf, L)` may return **fewer** than `L` bytes, because only some
have arrived so far. So you must **loop**, adding up what each `read` gives,
until you have them all. In Part 4 we write exactly these helpers:

- `readExactly(fd, n, out)`: keep calling `read` until `n` bytes have arrived.
- `writeAll(fd, data)`: keep calling `write` until all of `data` is accepted.

The final event-loop server does the same thing in a different way, by
collecting bytes in a buffer until a whole frame is there.
:::

:::quiz The client sends a 10-byte frame and then a 7-byte frame. The server's single read returns 13 bytes. What does it do?
It parses the first frame (the 4-byte length says 6, so 4 + 6 = 10 bytes),
handles it, and removes those 10 bytes. The 3 bytes left over are the
**start** of the second frame. It keeps them and waits for the remaining 4
bytes from a later read. It must **never** throw leftover bytes away.
:::

:::quiz Why is "it worked when I tested it" not good enough for network code?
On loopback with tiny messages, reads often happen to line up with writes.
Under real load, over real networks or with big messages, they don't. Code
must handle **any** split, and our unit tests will deliberately feed
incomplete data to make sure it does.
:::

:::recap
- TCP is a **byte stream**: `write` boundaries are not preserved.
- `read`/`write` may move **fewer bytes** than asked.
- Fix: **framing**. We use `[4-byte length][payload]` and only process complete frames, keeping leftovers.
:::
