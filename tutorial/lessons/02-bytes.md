---
title: Bytes, fixed-size integers and endianness
module: C++ toolkit
time: 30 min
---

:::goal
A network only carries **bytes**. Before we send anything, you need to be
comfortable thinking in bytes: what a byte is, how a number is stored as
several bytes, how to write numbers in **hex**, and how to copy the raw bytes
of a number into a `string` and back.
:::

## Everything is bytes

A **byte** is 8 bits, so it holds a number from 0 to 255. Memory is just a
very long array of bytes. Every variable you've ever made lives somewhere in
that array:

```text
memory:   ... | 0x48 | 0x69 | 0x00 | 0x2a | 0x00 | 0x00 | 0x00 | ...
                 'H'    'i'    '\0' └──── one int = 42 (4 bytes) ───┘
```

A `char` is 1 byte. An `int` is usually 4 bytes. A network connection is a
pipe that carries bytes from one program to another, nothing more. So to send
the number 42 to another program, we must answer two questions:

1. **How many bytes** does the number take?
2. **In what order** do those bytes go?

## Question 1: how many bytes? Fixed-size integers

In DSA you used `int` and `long long` without thinking about their size. But
the C++ standard does **not** fix the size of `int` or `long`. On some
machines `long` is 4 bytes, on others it's 8. If the client thinks a length
takes 8 bytes and the server reads 4, everything breaks.

The header `<cstdint>` gives us types with an **exact** size. We only need
two of them:

| Type | Size | Range | We use it for |
|---|---|---|---|
| `uint32_t` | 4 bytes | 0 … ~4.29 billion | lengths and counts in our protocol |
| `uint64_t` | 8 bytes | 0 … ~1.8 × 10¹⁹ | hash values |

The `u` means **unsigned**: no negative numbers. Lengths can never be
negative, so unsigned types fit them well.

:::cpp `size_t`
You've already met `size_t`: it's what `v.size()` and `s.size()` return. It's
an unsigned number big enough for the size of anything in memory. We use it
for sizes and positions inside strings.
:::

## Hexadecimal: the byte-friendly way to write numbers

Hex is base 16, using digits `0-9` and `a-f`. In C++ you write it with a
`0x` prefix. **One byte is always exactly two hex digits**, which is why
programmers love it:

| Decimal | Hex | Binary |
|---|---|---|
| 0 | `0x00` | `0000 0000` |
| 10 | `0x0a` | `0000 1010` |
| 42 | `0x2a` | `0010 1010` |
| 255 | `0xff` | `1111 1111` |

So `0x01020304` is a 4-byte number whose bytes are `01`, `02`, `03`, `04`.
You can see each byte without any arithmetic.

## Question 2: in what order? Endianness

A `uint32_t` takes 4 bytes in memory. Which byte comes first?

- **Little-endian**: the *least* significant byte (the "small end") comes
  first. Every Intel/AMD and Apple/ARM CPU you'll use works this way.
- **Big-endian**: the *most* significant byte comes first. This is how
  humans write numbers, and it's the traditional order for network headers,
  so it's also called **network byte order**.

```text
the number 0x01020304 stored in memory:

address:          +0    +1    +2    +3
little-endian:    04    03    02    01     <- your laptop
big-endian:       01    02    03    04     <- "network byte order"
```

:::analogy
Writing a date as `2025-03-14` (biggest unit first) is big-endian. Writing
`14-03-2025` (smallest unit first) is little-endian. Same date, different
order. Both sides just have to agree.
:::

:::why Which order does our project use?
**Our own protocol sends integers in the CPU's native order (little-endian),
exactly as they sit in memory.** It's simpler, and every machine we care
about is little-endian. The book *Build Your Own Redis* makes the same
choice. But the **operating system's socket functions** want port numbers and
IP addresses in **big-endian**, so in a later lesson we'll meet
`htons()`/`htonl()`, which convert to big-endian.
:::

## Copying the raw bytes of a number

We'll keep bytes in a plain `string`. A `string` is just a list of `char`s,
and a `char` is one byte, so a string can hold **any** bytes, even 0.

To put a number's 4 bytes into a string, we tell C++ "look at `v` as if it
were 4 chars":

```cpp
uint32_t v = 0x01020304;
string bytes((char *)&v, 4);   // a string made of v's 4 raw bytes
```

- `&v` is "the address of `v`", where it lives in memory. (Pointers are the
  next lesson.)
- `(char *)` is a **cast**: "treat that address as the address of chars".
- `string(pointer, 4)` builds a string from the 4 bytes starting there.

Going back is the mirror image. `copy` copies bytes out of a string into
memory we give it:

```cpp
uint32_t back;
bytes.copy((char *)&back, 4);  // copy 4 bytes from the string into back
```

:::why Why not just `bytes += v;`?
That would squash the number into a **single** char (keeping only the lowest
8 bits). We want all 4 bytes, untouched. This exact trick is how our protocol
will read and write lengths.
:::

:::task Peek at the bytes of a number
Write `scratch/bytes.cpp` that:

1. Prints the `sizeof` of `uint32_t` and `uint64_t`.
2. Stores `0x01020304` in a `uint32_t`, copies its 4 bytes into a string, and
   prints each byte as a number (`(int)b` turns a char into a printable number).
3. Copies the bytes back into a new `uint32_t` and prints it next to the
   original.

```bash
$ c++ -std=c++17 -Wall scratch/bytes.cpp -o build/bytes
$ build/bytes
```
:::

```output
uint32_t: 4 bytes
uint64_t: 8 bytes
bytes in memory: 4 3 2 1
read back: 16909060 (same as 16909060)
```

Notice `4 3 2 1`: the smallest byte came first. Your machine is
little-endian! (`16909060` is `0x01020304` written in decimal.)

:::hint Hint: includes
You need `<cstdint>` for the integer types, `<iostream>` for `cout` and
`<string>` for `string`.
:::

:::solution
@include code/a-basics/bytes.cpp title=scratch/bytes.cpp
:::

:::quiz On a little-endian machine, what bytes does `uint32_t n = 5;` occupy in memory?
`05 00 00 00`. The smallest byte (5) comes first, and the three higher bytes
are zero. You'll see exactly this pattern later when you inspect our protocol:
a length of 5 is sent as `05 00 00 00`.
:::

:::recap
- Networks carry **bytes**. Numbers must be turned into a fixed number of
  bytes in an agreed order.
- `uint32_t`/`uint64_t` have exact sizes. `size_t` is for sizes.
- Your CPU is **little-endian**. Our protocol uses that order. The socket API
  wants **big-endian** ("network order") for ports and IPs.
- `string((char *)&v, 4)` copies a number's bytes into a string, and
  `s.copy((char *)&v, 4)` copies them back.
:::
