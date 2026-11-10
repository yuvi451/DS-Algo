---
title: Responses and status codes
module: The protocol
time: 30 min
---

:::goal
Encode and parse the server's replies: a **1-byte status** (`RES_OK`,
`RES_ERR`, `RES_NX`) optionally followed by data. You'll meet `enum` and
default arguments.
:::

## Status codes with `enum`

A status is one of three values. We could use plain numbers 0, 1, 2, but
then `if (status == 2)` means nothing to a reader. An **enum** gives the
numbers names:

```cpp
// First byte of every response.
enum Status { RES_OK = 0, RES_ERR = 1, RES_NX = 2 };  // NX = key not found
```

`Status` is now a type, and `RES_OK`, `RES_ERR`, `RES_NX` are just the
numbers 0, 1 and 2 with readable names. Put it near the top of
`protocol.h`, after the constants.

## Encoding a response

```cpp
string encodeResponse(Status status, const string &data) {
    string out;
    out += (char)status;          // the status as a single byte
    if (!data.empty()) {
        appendU32(out, data.size());
        out += data;
    }
    return out;
}
```

`(char)status` turns the status number into one `char` (one byte), so `+=`
adds exactly one byte.

In the header it's declared with a **default argument**:

```cpp
// Response payload: [status byte] then, only if data is non-empty, [len][bytes].
// So an empty value looks the same on the wire as "no value".
string encodeResponse(Status status, const string &data = "");
```

:::cpp Default arguments
`const string &data = ""` means: if the caller leaves `data` out, use an
empty string. So both of these work:

```cpp
encodeResponse(RES_OK, "bar");   // status + data
encodeResponse(RES_NX);          // status only
```

The default goes **only in the declaration** (the header), not repeated in
the `.cpp` definition. Writing it in both places is a compile error.
:::

## Parsing a response

The client needs **two** results: the status and the data. So the parser
fills in two output parameters and returns whether it worked:

```cpp
bool parseResponse(const string &payload, Status &status, string &data) {
    if (payload.empty()) return false;                 // no status byte
    status = (Status)payload[0];
    data = "";
    if (payload.size() == 1) return true;              // status only
    if (payload.size() < 5 || 5 + readU32(payload, 1) != payload.size()) return false;
    data = payload.substr(5);                          // everything after [status][len]
    return true;
}
```

```text
offset:  0        1             5
         │ status │ len (4 B)   │ data (len bytes) │
         └ 1 B ───┴─────────────┴──────────────────┘   total must equal 5 + len
```

:::why Why check `5 + len != size` exactly, rather than just `<`?
We want the payload to be **exactly** status + length + data, with nothing
missing and nothing extra. An exact match catches both truncated and
oversized replies. Same "trust nothing" rule as the request parser.
:::

:::task Add responses to the protocol
1. `protocol.h`: add the `Status` enum after the constants, and after the
   request declarations add `encodeResponse` (with its comment) and
   `bool parseResponse(const string &payload, Status &status, string &data);`
2. `protocol.cpp`: add both functions after `parseRequest`.
3. `test_protocol.cpp`: add these two tests and call them from `main`:

```cpp
void testResponseRoundtripWithData() {
    string payload = encodeResponse(RES_OK, "bar");
    Status status;
    string data;
    assert(parseResponse(payload, status, data));
    assert(status == RES_OK);
    assert(data == "bar");
    cout << "testResponseRoundtripWithData: OK" << endl;
}

void testResponseRoundtripStatusOnly() {
    string payload = encodeResponse(RES_NX);
    Status status;
    string data;
    assert(parseResponse(payload, status, data));
    assert(status == RES_NX);
    assert(data.empty());
    cout << "testResponseRoundtripStatusOnly: OK" << endl;
}
```

```bash
$ c++ -std=c++17 -Wall test/test_protocol.cpp src/protocol.cpp -o build/test_protocol
$ build/test_protocol
```
:::

```output
testU32Roundtrip: OK
testRequestRoundtrip: OK
testRequestRejectsTruncated: OK
testResponseRoundtripWithData: OK
testResponseRoundtripStatusOnly: OK
All protocol tests passed.
```

:::solution
@include code/d-protocol/s3/src/protocol.h
@include code/d-protocol/s3/src/protocol.cpp
@include code/d-protocol/s3/test/test_protocol.cpp
:::

:::quiz Why does `encodeResponse(RES_OK, "")` produce the same bytes as `encodeResponse(RES_OK)`?
Because the data part is only written `if (!data.empty())`. An empty value
and "no value" both become the single byte `00`. That's the known quirk from
the design lesson: the client can't tell `set k ""` + `get k` apart from a
plain `OK`.
:::

:::recap
- `enum Status { RES_OK = 0, RES_ERR = 1, RES_NX = 2 };` gives the status numbers names.
- `encodeResponse(status, data = "")`: one status byte, then `[len][bytes]` only if data is non-empty.
- `parseResponse` fills `status` and `data`, and demands exact lengths.
- Default arguments live in the declaration only.
:::
