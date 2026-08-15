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
    buf.append(std::string_view("hello world"));
    buf.consume(6);
    assert(buf.size() == 5);
    assert(std::memcmp(buf.data(), "world", 5) == 0);
    printf("testBufferConsume: OK\n");
}

static void testRequestRoundtrip() {
    std::vector<std::string> args = {"set", "foo", "bar"};

    Buffer out;
    assert(encodeRequest(out, args));

    auto parsed = parseRequest(out.data(), out.size());
    assert(parsed.has_value());
    assert(parsed->size() == 3);
    assert((*parsed)[0] == "set");
    assert((*parsed)[1] == "foo");
    assert((*parsed)[2] == "bar");

    printf("testRequestRoundtrip: OK\n");
}

static void testRequestRejectsTruncated() {
    uint8_t bad[4];
    uint32_t n = 5;
    std::memcpy(bad, &n, 4);
    auto parsed = parseRequest(bad, 4);
    assert(!parsed.has_value());
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
    uint32_t l = static_cast<uint32_t>(payload.size());
    framed.append(reinterpret_cast<uint8_t *>(&l), 4);
    framed.append(payload.data(), payload.size());

    FrameInfo info{};
    assert(tryParseFrame(framed.data(), 4, info) == FrameStatus::Incomplete);
    assert(tryParseFrame(framed.data(), 4 + payload.size() - 1, info) == FrameStatus::Incomplete);

    FrameStatus rv = tryParseFrame(framed.data(), framed.size(), info);
    assert(rv == FrameStatus::Complete);
    assert(info.frameLen == framed.size());
    assert(info.payloadLen == payload.size());
    assert(info.payloadOff == 4);

    printf("testTryParseFrame: OK\n");
}

static void testTryParseFrameRejectsOversized() {
    uint8_t buf[4];
    uint32_t huge = K_MAX_MSG + 1;
    std::memcpy(buf, &huge, 4);
    FrameInfo info{};
    assert(tryParseFrame(buf, 4, info) == FrameStatus::Malformed);
    printf("testTryParseFrameRejectsOversized: OK\n");
}

static void testFrameIoOverSocketpair() {
    int fds[2];
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, fds) == 0);

    assert(writeFrame(fds[0], reinterpret_cast<const uint8_t *>("ping"), 4));

    auto got = readFrame(fds[1]);
    assert(got.has_value());
    assert(got->size() == 4 + 4);
    assert(std::memcmp(got->data() + 4, "ping", 4) == 0);

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
