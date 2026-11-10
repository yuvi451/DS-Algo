---
title: Glossary
module: Reference
time: lookup
---

Every term used in the course, in plain English. Use the sidebar search box
to jump to lessons that mention a term.

## Networking

| Term | Meaning |
|---|---|
| **Client / server** | The server waits at a known address. Clients connect to it and send requests. |
| **IP address** | Identifies a machine (network interface). IPv4 = 4 bytes, like `192.168.1.10`. |
| **Loopback, `127.0.0.1`, localhost** | "This same machine". Traffic never leaves your computer. `INADDR_LOOPBACK` in code. |
| **Port** | 16-bit number picking a program on a machine. Our server uses 1234 (`PORT`). |
| **Ephemeral port** | Random port the OS assigns to a client during `connect()`. |
| **4-tuple** | (client IP, client port, server IP, server port): uniquely identifies one TCP connection. |
| **TCP** | Reliable, ordered **byte stream** between two programs. |
| **UDP** | Unreliable, unordered, message-based. Not used here. |
| **Byte stream** | Data with no built-in message boundaries. Writes can be split or merged on arrival. |
| **Framing** | Marking where each message starts and ends in a byte stream. We use a 4-byte length prefix. |
| **Frame** | `[u32 length][payload]`. |
| **Protocol** | The agreed format of bytes between client and server. |
| **Serialization** | Turning structured data (a list of strings) into bytes. Parsing is the reverse. |
| **Handshake** | SYN / SYN-ACK / ACK, done by the kernel before a connection is usable. |
| **EOF** | End of file/stream. `read()` returns 0 when the peer closed the connection. |
| **TIME_WAIT** | State a closed connection lingers in for 30–60 s. The reason for `SO_REUSEADDR`. |
| **Nagle's algorithm** | TCP delaying small writes to batch them. Disabled with `TCP_NODELAY`. |
| **Pipelining** | Sending several requests before reading replies. The server must handle many requests per read. |
| **Network byte order** | Big-endian. Required by `sin_port`/`sin_addr`, converted with `htons`/`htonl`. |
| **RESP** | Real Redis's text protocol. We use a simpler binary one instead. |

## Operating system

| Term | Meaning |
|---|---|
| **Kernel** | The core of the OS. Owns hardware and the network stack. |
| **System call (syscall)** | A function that asks the kernel to do something: `read`, `write`, `socket`, `poll`… |
| **File descriptor (fd)** | Small integer naming an open file/socket in your process. Lowest free number is reused. |
| **stdin/stdout/stderr** | fds 0, 1, 2. |
| **Socket** | Kernel object for network I/O, used through an fd. |
| **Listening socket** | Created by `bind` + `listen`. Only used to `accept` new connections. |
| **Connection socket** | One per connected client (from `accept`) or per `connect`. Carries data. |
| **Backlog** | Kernel queue of fully connected clients waiting for `accept()`. |
| **Kernel send/receive buffers** | Where `write` copies data to and `read` copies data from. The cause of partial reads/writes. |
| **Blocking** | A call that waits (sleeps) until it can complete. |
| **Non-blocking (`O_NONBLOCK`)** | Calls never wait. They return `-1`/`EAGAIN` instead. |
| **`errno`** | Global error code set when a syscall returns -1. Only valid right after a failure. |
| **`EAGAIN`** | "Not ready, try again later" on a non-blocking fd. Not a real error. (`EWOULDBLOCK` is the same thing.) |
| **`EINTR`** | A blocking call was interrupted by a signal. Just retry. |
| **Signal** | Asynchronous OS notification to a process (`SIGPIPE`, `SIGINT` from Ctrl+C…). |
| **`SIGPIPE`** | Sent when writing to a closed connection. Kills the process by default, so we ignore it. |
| **Readiness notification** | Asking the kernel which fds can be read or written without blocking: `poll`, `epoll`, `kqueue`, `select`. |
| **`POLLIN` / `POLLOUT` / `POLLERR` / `POLLHUP`** | Readable / writable / error / hung up. |
| **Level-triggered** | `poll` keeps reporting an fd as ready as long as the condition holds. |
| **Event loop** | One thread: wait for ready fds → handle each without blocking → repeat. |
| **`socketpair`** | Two connected local sockets, handy for tests. |

## C++

| Term | Meaning |
|---|---|
| **`uint32_t` / `uint64_t`** | Unsigned integers of exactly 4 / 8 bytes (`<cstdint>`). |
| **`size_t`** | Unsigned type for sizes and positions. What `.size()` returns. |
| **Endianness** | Byte order of multi-byte numbers. Little-endian = smallest byte first (your CPU). |
| **Pointer / `*` / `&` / `->`** | Address holder / dereference / address-of / member through pointer. |
| **`nullptr`** | A pointer that points at nothing. |
| **Reference (`T &`)** | Another name for an existing variable. `const T &` = read-only, no copy. |
| **Output parameter** | A `&` parameter the function fills in, e.g. `bool get(const string &key, string &val)`. |
| **`new` / `delete`** | Create an object that lives until you free it / free it. |
| **Linked list** | Nodes that each point at the next one. Our hashtable buckets are linked lists. |
| **`struct` with methods** | Variables plus functions that work on them. `Name::method` defines one outside the struct. |
| **Cast `(T)x`** | Treat a value as another type: `(char *)&v` = "look at v as raw bytes", `(sockaddr *)&addr`. |
| **`enum`** | Named numbers: `enum Status { RES_OK = 0, RES_ERR = 1, RES_NX = 2 };`. |
| **`const` constant** | A named value that never changes, like `MAX_MSG`. |
| **Default argument** | `f(int x, const string &data = "")`: the caller may leave `data` out. |
| **`using namespace std;`** | Lets you write `string` instead of `std::string`. Write `::bind` for the OS's `bind`. |
| **`#pragma once`** | First line of a header: "only include this file once". |
| **Linker** | Joins compiled `.cpp` files into one program. "Undefined symbol" = a missing `.cpp`. |
| **`assert(cond)`** | Stop the program with the file and line if `cond` is false. Used in tests. |
| **`thread`** | Runs a function in parallel. `join()` waits for it to finish. |
| **Undefined behavior** | Code the C++ rules don't define, e.g. using memory after `delete`. Anything can happen. |

## Data structures

| Term | Meaning |
|---|---|
| **Chaining hashtable** | Array of buckets, each a linked list of entries. |
| **Bucket / slot** | One array position in a hashtable. |
| **Collision** | Different keys landing in the same bucket. |
| **Node** | One key-value pair in our hashtable, with its saved hash and a `next` pointer. |
| **Load factor** | keys ÷ buckets = average chain length. We resize at 8. |
| **Mask** | `buckets - 1` for power-of-two sizes. `hash & mask` = bucket index. |
| **FNV-1a** | Simple fast hash: start at the offset basis, per byte XOR then multiply by the FNV prime. |
| **Rehashing / resizing** | Moving entries into a bigger table. |
| **Progressive rehashing** | Moving at most 128 entries per operation, so no single call is slow. |
| **Throughput / latency / p99** | Ops per second / time per op / the time 99% of ops beat. |
