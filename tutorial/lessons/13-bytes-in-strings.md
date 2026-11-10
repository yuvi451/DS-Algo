---
title: "Bytes in a string, and your first unit test"
module: The protocol
time: 40 min
---

:::goal
Start the real project. Create `src/protocol.h` and `src/protocol.cpp` with
the project's constants and two tiny helpers that put a 4-byte number into a
`string` and read it back. Then write `test/test_protocol.cpp` to prove they
work.
:::

## A `string` is our byte buffer

Look back at the framing rules: data arrives in arbitrary chunks, and we must
**keep leftovers** until a whole frame is there. Outgoing replies also queue
up until the socket accepts them. Both cases need a **queue of bytes**:

```text
 add at the back ──►  [ bytes waiting to be processed ]  ──► remove from the front
```

A plain `string` does all of this already. A string is a list of `char`s, a
`char` is one byte, and a string can hold **any** byte value, even 0:

| What we need | `string` code |
|---|---|
| add bytes at the back | `buf += more;` or `buf.append(ptr, n);` |
| look at the bytes | `buf[i]`, `buf.size()`, `buf.substr(pos, len)` |
| drop the first `n` bytes | `buf.erase(0, n);` |
| the raw memory (for `write()`) | `buf.data()` |

:::warn Known performance trade-off
`erase(0, n)` shifts every remaining byte to the left, so it costs O(length)
each time. With many small requests in one buffer that adds up. A faster
buffer would just remember a "start" position. Our project keeps the simple
version and lists it under *known limitations*. It's a nice exercise once you
finish the course.
:::

## Numbers in and out of a string

Our protocol is full of 4-byte lengths, so we need two helpers. They use the
trick from the bytes lesson:

```cpp
void appendU32(string &out, uint32_t v) {
    out.append((char *)&v, 4);  // look at v as 4 raw bytes and copy them
}

uint32_t readU32(const string &s, size_t pos) {
    uint32_t v;
    s.copy((char *)&v, 4, pos);  // copy 4 bytes from s[pos] into v
    return v;
}
```

- `appendU32` adds the 4 bytes of `v` to the end of `out`, in the CPU's
  (little-endian) order. That's exactly our wire format.
- `readU32` copies the 4 bytes starting at position `pos` back into a
  number.

## The header: `src/protocol.h`

```cpp
#pragma once

#include <cstdint>
#include <string>
#include <vector>
using namespace std;

const size_t MAX_MSG = 4096;  // biggest payload we accept
const size_t HEADER_LEN = 4;  // the length in front of every message
const int PORT = 1234;

void appendU32(string &out, uint32_t v);        // add v's 4 bytes to the end of out
uint32_t readU32(const string &s, size_t pos);  // read 4 bytes starting at s[pos]
```

:::cpp `const` constants
`const size_t MAX_MSG = 4096;` is a named number that can never change.
Putting constants in the header lets the client and server share them, and
`PORT` replaces the hard-coded `1234` from Part 3. Writing them in CAPITALS
is a common way to say "this is a constant".
:::

## Unit tests

A **unit test** is a small program that calls your code with known inputs and
checks the results. We use plain `assert` (from `<cassert>`): if the
condition is false, the program **stops immediately** and prints the file and
line.

```cpp
void testU32Roundtrip() {
    string s;
    appendU32(s, 5);
    assert(s.size() == 4);
    assert(s[0] == 5 && s[1] == 0 && s[2] == 0 && s[3] == 0);  // smallest byte first
    assert(readU32(s, 0) == 5);
    cout << "testU32Roundtrip: OK" << endl;
}
```

The test file includes the header as `"../src/protocol.h"`, a path relative
to the `test/` folder. Build it together with `protocol.cpp`:

```bash
$ c++ -std=c++17 -Wall test/test_protocol.cpp src/protocol.cpp -o build/test_protocol
$ build/test_protocol
```

:::why Why test something so small?
Because everything else builds on it. If `readU32` read the wrong position,
every protocol bug later would look mysterious. Small tests on small pieces
make bugs show up **where they are**, not three layers away.
:::

:::task Create the protocol files and test them
1. Create `src/protocol.h` exactly as above (type it).
2. Create `src/protocol.cpp`: `#include "protocol.h"`, then the two helpers.
3. Create `test/test_protocol.cpp` with includes `<cassert>`, `<iostream>`,
   `"../src/protocol.h"`, the test above, and a `main()` that calls it and
   prints `All protocol tests passed.`
4. Build and run it with the commands above.
:::

```output
testU32Roundtrip: OK
All protocol tests passed.
```

:::solution
@include code/d-protocol/s1/src/protocol.h
@include code/d-protocol/s1/src/protocol.cpp
@include code/d-protocol/s1/test/test_protocol.cpp
:::

:::quiz Break it on purpose: change the test to `assert(readU32(s, 0) == 6);`. What happens?
The program stops with a message like
`Assertion failed: (readU32(s, 0) == 6), function testU32Roundtrip, file test_protocol.cpp, line 12.`
That's the safety net doing its job. Change it back afterwards!
:::

:::recap
- A `string` is our byte buffer: `+=`/`append` at the back, `erase(0, n)` from the front.
- `appendU32` / `readU32` move 4-byte numbers in and out of a string.
- Shared constants (`MAX_MSG`, `HEADER_LEN`, `PORT`) live in `protocol.h`.
- Tests use `assert` and print `OK` when they pass.
:::
