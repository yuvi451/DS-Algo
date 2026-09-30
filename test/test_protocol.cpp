#include <cassert>
#include <cstdio>
#include <cstring>

#include <sys/socket.h>
#include <unistd.h>

#include "../src/protocol.h"

static void testBufferAppendGrows() {
    Buffer buf;
    for (int i = 0; i < 1000; i++) {
        uint8_t b = static_cast<uint8_t>(i);
        buf.append(&b, 1);
    }
    assert(buf.size() == 1000);
    for (int i = 0; i < 1000; i++) {
        assert(buf.data()[i] == static_cast<uint8_t>(i));
    }
    printf("testBufferAppendGrows: OK\n");
}

static void testBufferConsume() {
    Buffer buf;
    buf.append("hello world");
    buf.consume(6);
    assert(buf.size() == 5);
    assert(std::memcmp(buf.data(), "world", 5) == 0);
    printf("testBufferConsume: OK\n");
}

static void testRequestRoundtrip() {
    Buffer out;
    assert(encodeRequest(out, {"set", "foo", "bar"}));

    auto parsed = parseRequest(out.data(), out.size());
    assert(parsed.has_value());
    assert((*parsed == std::vector<std::string>{"set", "foo", "bar"}));
    printf("testRequestRoundtrip: OK\n");
}

static void testRequestRejectsTruncated() {
    uint8_t bad[4];
    uint32_t nargs = 5;  // claims 5 args, provides none
    std::memcpy(bad, &nargs, 4);
    assert(!parseRequest(bad, 4).has_value());
    printf("testRequestRejectsTruncated: OK\n");
}

static void testResponseRoundtripWithData() {
    Buffer out;
    encodeResponse(out, ResponseStatus::Ok, "bar");

    auto resp = parseResponse(out.data(), out.size());
    assert(resp.has_value());
    assert(resp->status == ResponseStatus::Ok);
    assert(resp->data == "bar");
    printf("testResponseRoundtripWithData: OK\n");
}

static void testResponseRoundtripStatusOnly() {
    Buffer out;
    encodeResponse(out, ResponseStatus::Nx);

    auto resp = parseResponse(out.data(), out.size());
    assert(resp.has_value());
    assert(resp->status == ResponseStatus::Nx);
    assert(resp->data.empty());
    printf("testResponseRoundtripStatusOnly: OK\n");
}

static void testTryParseFrame() {
    Buffer payload;
    encodeResponse(payload, ResponseStatus::Ok, "hi");
    Buffer framed;
    appendFrame(framed, payload);

    size_t payloadLen = 0;
    assert(tryParseFrame(framed.data(), kHeaderLen, payloadLen) == FrameStatus::Incomplete);
    assert(tryParseFrame(framed.data(), framed.size() - 1, payloadLen) == FrameStatus::Incomplete);
    assert(tryParseFrame(framed.data(), framed.size(), payloadLen) == FrameStatus::Complete);
    assert(payloadLen == payload.size());
    assert(kHeaderLen + payloadLen == framed.size());
    printf("testTryParseFrame: OK\n");
}

static void testTryParseFrameRejectsOversized() {
    uint8_t buf[4];
    uint32_t huge = kMaxMsg + 1;
    std::memcpy(buf, &huge, 4);
    size_t payloadLen = 0;
    assert(tryParseFrame(buf, 4, payloadLen) == FrameStatus::Malformed);
    printf("testTryParseFrameRejectsOversized: OK\n");
}

static void testFrameIoOverSocketpair() {
    int fds[2];
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, fds) == 0);

    Buffer payload;
    payload.append("ping");
    assert(writeFrame(fds[0], payload));

    auto got = readFrame(fds[1]);
    assert(got.has_value());
    assert(got->size() == 4);
    assert(std::memcmp(got->data(), "ping", 4) == 0);

    close(fds[0]);
    close(fds[1]);
    printf("testFrameIoOverSocketpair: OK\n");
}

int main() {
    testBufferAppendGrows();
    testBufferConsume();
    testRequestRoundtrip();
    testRequestRejectsTruncated();
    testResponseRoundtripWithData();
    testResponseRoundtripStatusOnly();
    testTryParseFrame();
    testTryParseFrameRejectsOversized();
    testFrameIoOverSocketpair();
    printf("All protocol tests passed.\n");
    return 0;
}
