---
title: Encoding and parsing requests
module: The protocol
time: 45 min
---

:::goal
Turn a command like `{"set", "foo", "bar"}` into bytes (**encode**), and
turn bytes back into the command (**parse**). Parsing data from the network
must **never trust it**. You'll write a parser that rejects every malformed
input safely.
:::

## Encoding a request

```cpp
string encodeRequest(const vector<string> &args) {
    string out;
    appendU32(out, args.size());
    for (const string &arg : args) {
        appendU32(out, arg.size());
        out += arg;
    }
    return out;
}
```

It follows the format directly: the count, then `[len][bytes]` for each
argument. `for (const string &arg : args)` is the copy-free version of the
`for (auto x : v)` loop you know from DSA.

## Parsing: assume every byte is hostile

Parsing is where security bugs live. The bytes come from **some other
program**, which might be buggy or malicious. Every length must be checked
**before** we use it, or we'd read past the end of the data.

The parser can fail, so it returns `bool`, and on success it fills in the
caller's `args` (an **output parameter**, from the pointers lesson):

```cpp
bool parseRequest(const string &payload, vector<string> &args) {
    if (payload.size() < 4) return false;          // not even room for nargs
    uint32_t nargs = readU32(payload, 0);
    if (nargs > 1024) return false;                // absurd count: reject

    size_t pos = 4;                                // where we are reading now
    for (uint32_t i = 0; i < nargs; i++) {
        if (pos + 4 > payload.size()) return false;    // no room for this arg's length
        uint32_t len = readU32(payload, pos);
        pos += 4;
        if (pos + len > payload.size()) return false;  // claims more bytes than we have
        args.push_back(payload.substr(pos, len));
        pos += len;
    }
    return pos == payload.size();                  // no junk left over
}
```

Walk through it with the `set foo bar` payload (25 bytes):

```text
pos:  0           4           8        11          15       18          22       25
      03 00 00 00 │03 00 00 00│ s  e  t │03 00 00 00│ f  o  o │03 00 00 00│ b  a  r │
      nargs=3     │ len=3     │ arg 0   │ len=3     │ arg 1   │ len=3     │ arg 2   │ pos==size ✓
```

| Check | Rejects |
|---|---|
| `size < 4` | an empty or tiny payload |
| `nargs > 1024` | `nargs = 4 billion`: a client that wants us to loop forever |
| `pos + 4 > size` | a payload that ends in the middle of a length field |
| `pos + len > size` | a string that claims to be longer than the remaining bytes |
| `pos != size` | extra garbage after the last string |

`payload.substr(pos, len)` copies `len` bytes starting at `pos` into a new
string. That's one argument.

:::why Why not just separate the arguments with spaces?
Because a value might **contain** a space: `set greeting "hello world"`.
With length prefixes, any bytes at all can appear inside a string, and
parsing never gets confused.
:::

## Header additions

```cpp
// Request payload: [nargs] then [len][bytes] for each arg.
string encodeRequest(const vector<string> &args);
bool parseRequest(const string &payload, vector<string> &args);  // false if malformed
```

## The tests

```cpp
void testRequestRoundtrip() {
    string payload = encodeRequest({"set", "foo", "bar"});
    vector<string> args;
    assert(parseRequest(payload, args));
    assert(args.size() == 3);
    assert(args[0] == "set" && args[1] == "foo" && args[2] == "bar");
    cout << "testRequestRoundtrip: OK" << endl;
}

void testRequestRejectsTruncated() {
    string bad;
    appendU32(bad, 5);  // claims 5 args, provides none
    vector<string> args;
    assert(!parseRequest(bad, args));
    cout << "testRequestRejectsTruncated: OK" << endl;
}
```

A **round-trip** test encodes, then parses, and checks we got the original
back. The **truncated** test feeds a lie ("5 args!" but no data) and checks
the parser refuses it.

:::task Add requests to the protocol
1. `protocol.h`: add the two declarations above.
2. `protocol.cpp`: add `encodeRequest` and `parseRequest` after the helpers.
3. `test_protocol.cpp`: add both tests and call them from `main`.

```bash
$ c++ -std=c++17 -Wall test/test_protocol.cpp src/protocol.cpp -o build/test_protocol
$ build/test_protocol
```
:::

```output
testU32Roundtrip: OK
testRequestRoundtrip: OK
testRequestRejectsTruncated: OK
All protocol tests passed.
```

:::hint Hint: "use of undeclared identifier 'appendU32'"
In C++ a function must be declared **before** it's used. Since `appendU32` is
declared in `protocol.h` and `protocol.cpp` includes it at the top, this means
you forgot the `#include "protocol.h"`.
:::

:::solution
@include code/d-protocol/s2/src/protocol.h
@include code/d-protocol/s2/src/protocol.cpp
@include code/d-protocol/s2/test/test_protocol.cpp
:::

:::quiz What input would trip the `pos != size` check?
A valid request followed by extra bytes, e.g. `encodeRequest({"get", "x"}) + "zz"`.
Everything parses, but `pos` ends 2 bytes short of the size, so it returns
`false`.
:::

:::recap
- `encodeRequest`: `[nargs]` then `[len][bytes]` per argument.
- `parseRequest` checks **every** length against the remaining bytes, returns `bool`, and fills `args`.
- `substr(pos, len)` cuts one argument out of the payload.
:::
