---
title: Framing messages on the byte stream
module: The protocol
time: 30 min
---

:::goal
Implement the outer layer of the protocol: wrap any payload in a
`[length][payload]` **frame**, and check whether a pile of received bytes
contains a **complete** frame yet. This is the code that defeats the
byte-stream problem from Part 3.
:::

## Making a frame

Easy: the payload's size as 4 bytes, then the payload.

```cpp
string makeFrame(const string &payload) {
    string out;
    appendU32(out, payload.size());
    return out + payload;
}
```

## Checking for a complete frame

The receiver has a string of bytes that arrived so far. It asks: *is there a
whole frame at the front?* There are three possible answers, so a `bool`
isn't enough. Another `enum`:

```cpp
enum FrameResult { FRAME_INCOMPLETE, FRAME_TOO_BIG, FRAME_COMPLETE };
```

```cpp
// Is there a whole frame at the front of buf? Doesn't remove anything.
FrameResult tryParseFrame(const string &buf, size_t &payloadLen) {
    if (buf.size() < HEADER_LEN) return FRAME_INCOMPLETE;              // not even the 4-byte length
    payloadLen = readU32(buf, 0);
    if (payloadLen > MAX_MSG) return FRAME_TOO_BIG;                    // refuse
    if (buf.size() < HEADER_LEN + payloadLen) return FRAME_INCOMPLETE; // payload not all here yet
    return FRAME_COMPLETE;
}
```

(When you don't write numbers in an `enum`, they count up from 0 on their
own: `FRAME_INCOMPLETE` = 0, `FRAME_TOO_BIG` = 1, `FRAME_COMPLETE` = 2.)

```text
buffer contents                            result
────────────────────────────────────────   ────────────────────────────
08 00                                      INCOMPLETE (only 2 of 4 header bytes)
08 00 00 00 00 03 00                       INCOMPLETE (need 4 + 8 = 12 bytes, have 7)
08 00 00 00 00 03 00 00 00 62 61 72        COMPLETE, payloadLen = 8
08 00 00 00 00 03 00 00 00 62 61 72 05 …   COMPLETE, payloadLen = 8 (rest is the next frame)
ff ff 00 00 …                              TOO_BIG (65535 > 4096)
```

The function returns the result, and when it finds a length it also writes it
into the caller's `payloadLen` (an output parameter again):

```cpp
size_t len = 0;
if (tryParseFrame(buf, len) == FRAME_COMPLETE) {
    string payload = buf.substr(HEADER_LEN, len);   // the message itself
}
```

:::why Why doesn't it remove the frame from the buffer?
Keeping it a pure "look, don't touch" check makes it easy to test, and lets
the caller decide what to do. The server will handle the request, and only
then `erase` those bytes.
:::

## Header additions

```cpp
// Frame: [payload length][payload]. Every message on the socket is a frame.
string makeFrame(const string &payload);

enum FrameResult { FRAME_INCOMPLETE, FRAME_TOO_BIG, FRAME_COMPLETE };
FrameResult tryParseFrame(const string &buf, size_t &payloadLen);
```

:::task Add framing and test the tricky cases
1. Add the declarations above to `protocol.h` (after `parseResponse`).
2. Add `makeFrame` and `tryParseFrame` to `protocol.cpp`.
3. Add two tests to `test_protocol.cpp`:
   - `testTryParseFrame()`: frame the payload `encodeResponse(RES_OK, "hi")`,
     then assert:
     - only the first 3 bytes (`framed.substr(0, 3)`) → `FRAME_INCOMPLETE`
     - all bytes except the last → `FRAME_INCOMPLETE`
     - all bytes → `FRAME_COMPLETE`, `len == payload.size()`, and
       `HEADER_LEN + len == framed.size()`
   - `testTryParseFrameRejectsOversized()`: `appendU32(buf, MAX_MSG + 1)`
     and assert `FRAME_TOO_BIG`.

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
testTryParseFrame: OK
testTryParseFrameRejectsOversized: OK
All protocol tests passed.
```

:::hint Hint: testing "incomplete" without a socket
You don't need a network to test partial data. Just pass a **shorter**
string: `framed.substr(0, framed.size() - 1)` pretends the last byte hasn't
arrived yet.
:::

:::solution
@include code/d-protocol/s4/src/protocol.h
@include code/d-protocol/s4/src/protocol.cpp
@include code/d-protocol/s4/test/test_protocol.cpp
:::

:::recap
- `makeFrame(payload)` returns `[4-byte len][payload]`.
- `tryParseFrame` answers `FRAME_INCOMPLETE` / `FRAME_TOO_BIG` / `FRAME_COMPLETE`, and returns the payload length through a `&` parameter.
- Tests simulate partial arrival by passing a shorter string.
:::
