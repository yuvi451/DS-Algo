#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

constexpr size_t K_MAX_MSG = 4096;
constexpr uint16_t SERVER_PORT = 1234;

enum class ResponseStatus : uint8_t {
    Ok = 0,
    Err = 1,
    Nx = 2,
};

class Buffer {
public:
    void append(const uint8_t *data, size_t len);
    void append(std::string_view s);
    void consume(size_t n);

    const uint8_t *data() const { return buf_.data(); }
    size_t size() const { return buf_.size(); }
    bool empty() const { return buf_.empty(); }

private:
    std::vector<uint8_t> buf_;
};

bool encodeRequest(Buffer &out, const std::vector<std::string> &args);
std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len);

// When data is empty, the len/data fields are omitted entirely, so a
// RES_OK response for an empty-string value is indistinguishable on the
// wire from a RES_OK/RES_NX response with no value.
void encodeResponse(Buffer &out, ResponseStatus status, std::string_view data = {});

struct Response {
    ResponseStatus status;
    std::string data;
};
std::optional<Response> parseResponse(const uint8_t *data, size_t len);

enum class FrameStatus {
    Incomplete,
    Malformed,
    Complete,
};

struct FrameInfo {
    size_t frameLen;
    size_t payloadOff;
    size_t payloadLen;
};

FrameStatus tryParseFrame(const uint8_t *buf, size_t bufLen, FrameInfo &out);

bool readFull(int fd, uint8_t *buf, size_t n);
bool writeAll(int fd, const uint8_t *buf, size_t n);
std::optional<Buffer> readFrame(int fd);
bool writeFrame(int fd, const uint8_t *payload, size_t len);

#endif
