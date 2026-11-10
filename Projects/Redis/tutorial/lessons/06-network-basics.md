---
title: How two programs talk over a network
module: How networks work
time: 40 min
---

:::goal
Understand the ideas behind every line of networking code we'll write:
**clients and servers, IP addresses, ports, TCP vs UDP, and the layers** of a
network. Then make two programs talk using a ready-made tool, before writing
any code.
:::

## Clients and servers

Almost every networked program plays one of two roles:

| | **Server** | **Client** |
|---|---|---|
| Starts | first, and keeps running | whenever it wants something |
| Does | waits at a known address for others to connect | connects to that address |
| Example | Redis, a web server | `redis-cli`, a web browser |
| In this course | `build/server` | `build/client` |

:::analogy
A server is a **shop with a fixed address**. It opens in the morning and
waits. A client is a **customer** who walks to that address, asks for
something, gets an answer, and leaves. The shop must be open *before*
customers arrive. Same here: always start the server first.
:::

## Finding the right machine: IP addresses

Every machine on a network has an **IP address**. IPv4 addresses are 32-bit
numbers written as four bytes: `192.168.1.10`.

One address is special: **`127.0.0.1`, also called *loopback* or
*localhost***. It always means **"this same computer"**. Data sent to
`127.0.0.1` never leaves your machine. The operating system hands it straight
from one program to another.

**Our whole project runs on `127.0.0.1`.** Client and server are on the same
laptop, but they talk using exactly the same code they'd use across the
internet.

:::why Why only loopback?
Safety. Our toy database has no password. Binding to `127.0.0.1` means only
programs on your own computer can reach it. Nobody else on your Wi-Fi can
connect.
:::

## Finding the right program: ports

An IP address gets you to the right **machine**. But a machine runs many
programs: a browser, Spotify, our server… The **port**, a 16-bit number from
0 to 65535, picks the program.

:::analogy
IP address = the **building's street address**. Port = the **flat number**
inside the building.
:::

- Well-known services have fixed ports: web = 80/443, SSH = 22, real Redis = **6379**.
- **Our server listens on port `1234`.**
- A client doesn't choose its own port. The OS gives it a random free one
  (called an *ephemeral port*, e.g. `52311`) when it connects.

So a single connection is fully identified by **four numbers**, the
**4-tuple**:

```text
(client IP, client port, server IP, server port)
 127.0.0.1    52311      127.0.0.1    1234      ← connection A
 127.0.0.1    52312      127.0.0.1    1234      ← connection B (different client port)
```

That's how hundreds of clients can talk to the same server port at once:
each connection has a different client port.

## TCP vs UDP

On top of IP there are two main **transport protocols**:

| | **TCP** | **UDP** |
|---|---|---|
| Connection | Yes, a "handshake" first | No, just fire off packets |
| Lost data | Automatically re-sent | Lost forever |
| Order | Guaranteed | Not guaranteed |
| Shape of data | **A continuous stream of bytes** | Separate little packets |
| Used by | Web, databases, SSH, **Redis, our project** | Video calls, games, DNS |

A database must **never** lose or reorder a `set` command, so we use
**TCP**. The OS kernel does all the hard work for us: splitting data into
packets, re-sending lost ones, putting them back in order.

:::warn Remember this sentence, we'll come back to it
**TCP gives you a stream of bytes, not messages.** If the client sends
"hello" and then "world", the server might receive "helloworld" in one go, or
"hel" then "loworld". Part 3 shows this happening for real, and Part 4 is
about solving it.
:::

## The layers (only what we need)

Networking is built in layers. Each layer uses the one below it:

```text
 ┌───────────────────────────────────────────────┐
 │ Application: OUR PROTOCOL (what bytes mean)   │ ◄── the code WE write
 ├───────────────────────────────────────────────┤
 │ Transport: TCP (reliable, ordered bytes)      │ ┐
 │            + ports (which program)            │ │
 ├───────────────────────────────────────────────┤ │ done by the
 │ Network: IP (which machine, small packets)    │ │ operating system
 ├───────────────────────────────────────────────┤ │ (the "kernel")
 │ Link: Wi-Fi / Ethernet / loopback             │ ┘
 └───────────────────────────────────────────────┘
```

We only write the **top layer**. We hand bytes to the OS through an API
called **sockets** (coming up in two lessons), and the OS handles TCP and IP.

:::net What's the "kernel"?
The **kernel** is the core of the operating system. It controls the hardware
and runs the network stack. Your program can't touch the network card
directly. It asks the kernel through special functions called **system
calls**. Next lesson is all about them.
:::

## Hands-on: talk over TCP with `nc`

`nc` (netcat) is a tiny tool that connects your keyboard to a TCP
connection. We'll use it all course long to poke at our server.

:::task Chat between two terminals
1. In **terminal 1**, start a server that listens on port 1234:

```bash
$ nc -l 1234
```

It just waits. That's a server waiting for a client.

2. In **terminal 2**, connect to it as a client:

```bash
$ nc 127.0.0.1 1234
```

3. Type `hi server` in terminal 2 and press Enter. Then type something in
   terminal 1 and press Enter.
4. Press **Ctrl + C** in either terminal to hang up.
:::

```output
Terminal 1 shows:  hi server
Terminal 2 shows:  whatever you typed in terminal 1
```

You just made a TCP connection on loopback, port 1234. Our server will do
the same thing, but answer with data from its hashtable instead of from your
keyboard.

:::hint It says "Address already in use" or nothing happens
Something else is already using port 1234, maybe an old `nc` you didn't stop.
Find it with `lsof -iTCP:1234 -sTCP:LISTEN` and stop it with Ctrl + C in its
terminal, or `kill <PID>`. On Linux, if `nc -l 1234` complains, try
`nc -l -p 1234`.
:::

:::quiz Why must terminal 1 run first?
Terminal 1 is the server. If nothing is listening on port 1234 when the
client connects, the OS rejects the attempt immediately ("Connection
refused"). The shop must be open before customers arrive.
:::

:::quiz Two `nc` clients connect to the same server port. How does the OS keep their data apart?
Each connection has a different 4-tuple, because each client got a different
ephemeral port. The OS uses all four numbers to deliver each byte to the right
connection.
:::

:::recap
- **Server** waits at a known IP + port. **Client** connects to it.
- `127.0.0.1` (loopback) = this machine. Port `1234` = our server.
- **TCP**: reliable, ordered, but a **stream of bytes** with no message boundaries.
- We only write the application layer. The kernel does TCP/IP.
:::
