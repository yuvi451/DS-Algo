---
title: Designing our wire protocol
module: The protocol
time: 35 min
---

:::goal
Before writing code, design **exactly** which bytes travel between client and
server. A **protocol** is the contract both sides agree on. By the end of this
lesson you'll be able to decode a real message from raw hex by hand.
:::

## Two levels of structure

Our protocol answers two separate questions:

1. **Framing**: where does one message end and the next begin? (the
   byte-stream problem from last lesson)
2. **Serialization**: inside one message, how is a *list of strings* (a
   command like `set foo bar`) turned into bytes, and back?

```text
the TCP byte stream:
┌─────┬──────────────┬─────┬──────────────┬─────┬────────
│ len │   payload    │ len │   payload    │ len │  ...
└─────┴──────────────┴─────┴──────────────┴─────┴────────
  4 B   ← frame 1 →    4 B   ← frame 2 →
```

## Rule 1: the frame

```text
frame:  [len : 4 bytes][payload : len bytes]       len <= 4096
```

- `len` is a `uint32_t` in the CPU's byte order (little-endian on your laptop).
- The payload is at most **4096 bytes** (`MAX_MSG`). Anything bigger is
  treated as an attack or a bug, and the server hangs up.

:::why Why put a size limit on messages?
Without one, a buggy or malicious client could send the length `0xFFFFFFFF`
(4 GB). The server would try to buffer 4 GB and run out of memory. **Never
trust numbers that come from the network.** Check them against a limit
first.
:::

## Rule 2: the request payload

A command is a list of strings, like the words you type in a shell:
`["set", "foo", "bar"]`. We encode it as a count, then each string with its
own length:

```text
request:  [nargs : 4 B] then for each arg: [len : 4 B][bytes]       nargs <= 1024
```

Here is the **real** frame our client sends for `set foo bar` (29 bytes):

```text
19 00 00 00 │ 03 00 00 00 │ 03 00 00 00 73 65 74 │ 03 00 00 00 66 6f 6f │ 03 00 00 00 62 61 72
 frame len  │   nargs     │  len=3      s  e  t  │  len=3      f  o  o  │  len=3      b  a  r
   = 25     │   = 3       │                      │                      │
```

- `0x19` = 25: the payload is 4 + (4+3) × 3 = 25 bytes.
- `73 65 74` are the ASCII codes for `s`, `e`, `t`.
- Every number is 4 bytes, smallest byte first (little-endian).

:::why Why length-prefix each string? Why not separate them with spaces?
Because a value might **contain** a space: `set greeting "hello world"`.
With length prefixes, any bytes at all can appear inside a string, including
spaces, newlines or zero bytes, and parsing never gets confused.
:::

## Rule 3: the response payload

```text
response:  [status : 1 byte] then, only if there's data: [len : 4 B][bytes]
```

| Status byte | Name | Meaning |
|---|---|---|
| `0` | `RES_OK` | Success, maybe with a value |
| `1` | `RES_ERR` | Unknown command or wrong number of arguments |
| `2` | `RES_NX` | Key does not exist ("**n**ot e**x**ists") |

Real examples (shown as full frames):

```text
reply to "get foo" when foo = "bar":
08 00 00 00 │ 00     │ 03 00 00 00 62 61 72
 frame len  │ status │  len=3      b  a  r
   = 8      │ = OK   │

reply to "get foo" when foo doesn't exist:
01 00 00 00 │ 02
 frame len  │ status = NX
   = 1      │ (no data part at all)
```

## The commands

| Command | Server replies |
|---|---|
| `get k` | `RES_OK` + the value, or `RES_NX` if k doesn't exist |
| `set k v` | `RES_OK` |
| `del k` | `RES_OK` if k existed, otherwise `RES_NX` |
| anything else | `RES_ERR` |

:::why Why not use the real Redis protocol (RESP)?
Real Redis uses a text-based protocol, where lengths are written as decimal
text followed by `\r\n`. That's more fiddly to parse. Our binary format teaches
the same ideas (framing + serialization) with simpler code. The book *Build
Your Own Redis* makes the same choice. The price: the official `redis-cli`
can't talk to our server, so we write our own client.
:::

:::warn Known quirk (kept on purpose)
Because the data part is left out when the value is empty, `get k` after
`set k ""` looks exactly like a plain `RES_OK` with no data. Our client prints
`OK` in that case. It's documented in the project's README under known
limitations.
:::

## What we'll build in Part 4

All of this lives in two files shared by client and server:

```text
src/protocol.h     declarations: constants, encode/parse functions
src/protocol.cpp   definitions
test/test_protocol.cpp   unit tests that prove each piece works
```

| Lesson | Adds |
|---|---|
| 4.2 | Bytes in a `string`: `appendU32` / `readU32` |
| 4.3 | `encodeRequest` / `parseRequest` |
| 4.4 | `Status`, `encodeResponse` / `parseResponse` |
| 4.5 | `makeFrame` / `tryParseFrame` (framing) |
| 4.6 | Blocking socket helpers: `readExactly`, `writeAll`, `connectToServer`, `writeFrame`, `readFrame` |

:::quiz Decode this request payload: `02 00 00 00 03 00 00 00 64 65 6c 01 00 00 00 78`
`nargs` = 2. First string: length 3, bytes `64 65 6c` = `d e l`. Second
string: length 1, byte `78` = `x`. So the command is **`del x`**. (In the
ASCII table, `a`=0x61, `b`=0x62, … `x`=0x78.)
:::

:::quiz How many bytes is the whole frame for `get foo`?
Payload = 4 (nargs) + (4 + 3) for "get" + (4 + 3) for "foo" = 18. Frame =
4 + 18 = **22 bytes**.
:::

:::quiz A frame header arrives saying the length is 100,000. What should the server do?
100,000 > 4096 (`MAX_MSG`), so it's malformed. The server **closes the
connection** without trying to read or buffer it.
:::

:::recap
- **Frame** = `[u32 len][payload]`, len ≤ 4096.
- **Request** = `[u32 nargs]` then `[u32 len][bytes]` per argument, nargs ≤ 1024.
- **Response** = `[u8 status]` then `[u32 len][bytes]` only if there's data.
- All integers are little-endian, as they sit in memory. Never trust lengths from the network.
:::
