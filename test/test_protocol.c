#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include "../src/protocol.h"

static void test_buffer_append_grows(void) {
    Buffer buf;
    buf_init(&buf);
    for (int i = 0; i < 1000; i++) {
        uint8_t b = (uint8_t)i;
        buf_append(&buf, &b, 1);
    }
    assert(buf.len == 1000);
    for (int i = 0; i < 1000; i++) {
        assert(buf.data[i] == (uint8_t)i);
    }
    buf_free(&buf);
    printf("test_buffer_append_grows: OK\n");
}

static void test_buffer_consume(void) {
    Buffer buf;
    buf_init(&buf);
    buf_append(&buf, (const uint8_t *)"hello world", 11);
    buf_consume(&buf, 6);
    assert(buf.len == 5);
    assert(memcmp(buf.data, "world", 5) == 0);
    buf_free(&buf);
    printf("test_buffer_consume: OK\n");
}

static void test_request_roundtrip(void) {
    char *args[] = {"set", "foo", "bar"};
    size_t arglens[] = {3, 3, 3};

    Buffer out;
    buf_init(&out);
    assert(encode_request(&out, args, arglens, 3) == 0);

    char **parsed_args;
    size_t *parsed_lens;
    size_t nargs;
    assert(parse_request(out.data, out.len, &parsed_args, &parsed_lens, &nargs) == 0);
    assert(nargs == 3);
    assert(strcmp(parsed_args[0], "set") == 0);
    assert(strcmp(parsed_args[1], "foo") == 0);
    assert(strcmp(parsed_args[2], "bar") == 0);
    assert(parsed_lens[1] == 3);

    free_request_args(parsed_args, parsed_lens, nargs);
    buf_free(&out);
    printf("test_request_roundtrip: OK\n");
}

static void test_request_rejects_truncated(void) {
    uint8_t bad[4];
    uint32_t n = 5; /* claims 5 args but no data follows */
    memcpy(bad, &n, 4);
    char **args;
    size_t *lens;
    size_t nargs;
    assert(parse_request(bad, 4, &args, &lens, &nargs) == -1);
    printf("test_request_rejects_truncated: OK\n");
}

static void test_response_roundtrip_with_data(void) {
    Buffer out;
    buf_init(&out);
    encode_response(&out, RES_OK, (const uint8_t *)"bar", 3);

    ResponseStatus status;
    const uint8_t *data;
    size_t datalen;
    assert(parse_response(out.data, out.len, &status, &data, &datalen) == 0);
    assert(status == RES_OK);
    assert(datalen == 3);
    assert(memcmp(data, "bar", 3) == 0);

    buf_free(&out);
    printf("test_response_roundtrip_with_data: OK\n");
}

static void test_response_roundtrip_status_only(void) {
    Buffer out;
    buf_init(&out);
    encode_response(&out, RES_NX, NULL, 0);

    ResponseStatus status;
    const uint8_t *data;
    size_t datalen;
    assert(parse_response(out.data, out.len, &status, &data, &datalen) == 0);
    assert(status == RES_NX);
    assert(datalen == 0);

    buf_free(&out);
    printf("test_response_roundtrip_status_only: OK\n");
}

static void test_try_parse_frame(void) {
    Buffer payload;
    buf_init(&payload);
    encode_response(&payload, RES_OK, (const uint8_t *)"hi", 2);

    Buffer framed;
    buf_init(&framed);
    uint32_t l = (uint32_t)payload.len;
    buf_append(&framed, (uint8_t *)&l, 4);
    buf_append(&framed, payload.data, payload.len);

    size_t frame_len, payload_len;
    assert(try_parse_frame(framed.data, 4, &frame_len, &payload_len) == 0);
    assert(try_parse_frame(framed.data, 4 + payload.len - 1, &frame_len, &payload_len) == 0);

    int rv = try_parse_frame(framed.data, framed.len, &frame_len, &payload_len);
    assert(rv == 1);
    assert(frame_len == framed.len);
    assert(payload_len == payload.len);

    buf_free(&payload);
    buf_free(&framed);
    printf("test_try_parse_frame: OK\n");
}

static void test_try_parse_frame_rejects_oversized(void) {
    uint8_t buf[4];
    uint32_t huge = K_MAX_MSG + 1;
    memcpy(buf, &huge, 4);
    size_t frame_len, payload_len;
    assert(try_parse_frame(buf, 4, &frame_len, &payload_len) == -1);
    printf("test_try_parse_frame_rejects_oversized: OK\n");
}

static void test_frame_io_over_socketpair(void) {
    int fds[2];
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, fds) == 0);

    assert(write_frame(fds[0], (const uint8_t *)"ping", 4) == 0);

    Buffer got;
    buf_init(&got);
    assert(read_frame(fds[1], &got) == 0);
    assert(got.len == 4 + 4);
    assert(memcmp(got.data + 4, "ping", 4) == 0);

    buf_free(&got);
    close(fds[0]);
    close(fds[1]);
    printf("test_frame_io_over_socketpair: OK\n");
}

int main(void) {
    test_buffer_append_grows();
    test_buffer_consume();
    test_request_roundtrip();
    test_request_rejects_truncated();
    test_response_roundtrip_with_data();
    test_response_roundtrip_status_only();
    test_try_parse_frame();
    test_try_parse_frame_rejects_oversized();
    test_frame_io_over_socketpair();
    printf("All protocol tests passed.\n");
    return 0;
}
