---
title: System calls, file descriptors and errno
module: How networks work
time: 35 min
---

:::goal
Before touching sockets, learn the three ideas that **every** line of our
network code depends on: **system calls**, **file descriptors**, and how
system calls report **errors** (`-1` + `errno`). We'll practise on ordinary
files, because sockets work in exactly the same way.
:::

## System calls

Your program isn't allowed to touch the disk or network card directly. It
asks the kernel to do it, through **system calls** ("syscalls"). They look
like normal C functions:

| Syscall | Asks the kernel to… |
|---|---|
| `open()` | open a file |
| `read()` | give me bytes from something |
| `write()` | take these bytes |
| `close()` | I'm done with this |
| `socket()`, `bind()`, `listen()`, `accept()`, `connect()` | networking, next lesson |
| `poll()` | wake me up when something is ready, Part 5 |

They come from POSIX headers like `<unistd.h>` and `<fcntl.h>`, not from the
C++ standard library.

## File descriptors: tickets for open things

When you `open()` a file, the kernel doesn't give you the file. It gives you
a small **integer** called a **file descriptor (fd)**. You pass that number
back to `read`/`write`/`close` to say *which* open thing you mean.

:::analogy
An fd is a **coat-check ticket**. You hand over your coat (open a file or
connection) and get ticket #3. Later you say "ticket #3 please" and get the
right coat. The number itself means nothing outside your own program.
:::

Rules worth memorising:

- Every program starts with three fds already open:
  **0 = stdin** (keyboard), **1 = stdout** (screen), **2 = stderr** (screen, for errors).
- A new fd is always **the lowest free number**. So your first opened file
  or socket is usually **3**, the next **4**, and so on.
- When fd 4 is closed, the next new fd reuses **4**.

**In Unix, sockets are fds too.** A network connection is "something you can
`read()` and `write()`", just like a file. That's why this lesson matters.

## `read()` and `write()`

```cpp
int n = read(fd, buf, count);    // buf: where to put the bytes
int n = write(fd, buf, count);   // buf: the bytes to send
```

- `read` copies **up to** `count` bytes from fd into your buffer `buf`.
- `write` copies **up to** `count` bytes from `buf` to the fd.
- Both **return how many bytes they actually moved**, which **can be fewer
  than you asked for**.

| `read()` returns | Meaning |
|---|---|
| `> 0` | that many bytes were read |
| `0` | **end of file (EOF)**: no more data will ever come. For a network connection: **the other side closed it** |
| `-1` | error, look at `errno` |

:::cpp What can `buf` be?
Any memory: a `char buf[100]` array, or the inside of a string
(`s.data()`). `read` and `write` don't care about types, they just move
bytes. (The official return type is `ssize_t`, a signed size, but storing it
in an `int` is fine for our small reads.)
:::

## Errors: `-1` and `errno`

Syscalls signal failure by returning `-1`. To learn **why**, read the global
variable `errno` (from `<cerrno>`). It holds an error code like `ENOENT`
("no such file") or `EAGAIN` ("try again later", very important in Part 5).

`strerror(errno)` (from `<cstring>`) turns the code into readable text:

```cpp
cout << strerror(errno) << endl;   // No such file or directory
```

:::warn `errno` is only meaningful right after a failure
A successful call does **not** reset `errno` to 0. So check `errno` **only
when the call returned -1**. Our server does exactly this:
`if (n < 0 && errno == EAGAIN)`.
:::

:::task Explore fds with real files
Write `scratch/fds.cpp` that:

1. Uses `write(1, ...)` (fd 1 = stdout) to print `hello via write()` with
   no `cout`.
2. `open`s `notes.txt` for writing (create it if missing, empty it if it
   exists), prints the fd it got, writes `abc`, closes it.
3. Opens it again for reading, `read`s into a 100-byte buffer, prints how
   many bytes came back and the text, then reads **again** and prints that
   return value.
4. Tries to open `does/not/exist.txt`. When it fails, prints `errno` and
   `strerror(errno)`.

The `open` calls you need:

```cpp
int fd = open("notes.txt", O_CREAT | O_WRONLY | O_TRUNC, 0644);  // write
int fd = open("notes.txt", O_RDONLY);                            // read
```

```bash
$ c++ -std=c++17 -Wall scratch/fds.cpp -o build/fds
$ build/fds
```
:::

```output
hello via write()
notes.txt got fd 3
read returned 3: abc
read again returned 0 (0 means end of file)
errno is 2: No such file or directory
```

Notice that the first file got **fd 3**, because 0, 1 and 2 were taken. And
the second `read` returned **0**: end of file.

:::hint Hint: what are `O_CREAT | O_WRONLY | O_TRUNC` and `0644`?
They're **bit flags** combined with `|` (bitwise OR): *create* the file if
missing, open it *write-only*, and *truncate* (empty) it. `0644` sets the
file's permissions (owner can read/write, others can read). You'll combine
flags with `|` again for sockets and `poll()`.
:::

:::hint Hint: printing the bytes you read
`string(buf, n)` makes a string from exactly the first `n` bytes of `buf`, so
`cout << string(buf, n)` prints only what was read.
:::

:::solution
@include code/b-net/fds.cpp title=scratch/fds.cpp
:::

:::quiz Your server calls `read()` on a client's connection and gets 0. What happened?
The client **closed the connection** (EOF). No more data will ever come, so
the server should close its side too. Our server does exactly that:
`if (n <= 0) conn->wantClose = true;`
:::

:::recap
- Syscalls (`open`, `read`, `write`, `close`, …) ask the kernel to do I/O.
- A **file descriptor** is a small int naming an open file or socket. New fds take the lowest free number.
- `read`/`write` return bytes moved (maybe **fewer** than asked), `0` = EOF, `-1` = error.
- On `-1`, check `errno`. `strerror(errno)` turns it into text.
:::
