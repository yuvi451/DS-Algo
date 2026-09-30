#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

// All integers on the wire are 32-bit in host byte order (little-endian on
// x86/ARM). See README.md for the full message layout.
constexpr size_t kMaxMsg = 4096;
constexpr size_t kHeaderLen = 4;
constexpr uint16_t kServerPort = 1234;

enum class ResponseStatus : uint8_t {
    Ok = 0,
    Err = 1,
    Nx = 2,
};

class Buffer {
public:
    void append(const uint8_t *data, size_t len);
    void append(std::string_view s);
    void consume(size_t n);  // drop n bytes from the front

    const uint8_t *data() const { return buf_.data(); }
    size_t size() const { return buf_.size(); }

private:
    std::vector<uint8_t> buf_;
};

// Request payload: [nargs] then [len][bytes] per arg.
bool encodeRequest(Buffer &out, const std::vector<std::string> &args);  // false if > kMaxMsg
std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len);

// Response payload: [1-byte status] then, only if data is non-empty, [len][bytes].
// So an empty-string value looks the same on the wire as "no value".
void encodeResponse(Buffer &out, ResponseStatus status, std::string_view data = {});

struct Response {
    ResponseStatus status;
    std::string data;
};
std::optional<Response> parseResponse(const uint8_t *data, size_t len);

// Frame: [payload length][payload].
void appendFrame(Buffer &out, const Buffer &payload);

enum class FrameStatus {
    Incomplete,  // wait for more bytes
    Malformed,   // declared length exceeds kMaxMsg
    Complete,
};
FrameStatus tryParseFrame(const uint8_t *buf, size_t len, size_t &payloadLen);

// Blocking helpers used by the client and the load tester.
int connectToServer();  // -1 on failure, errno set
bool writeFrame(int fd, const Buffer &payload);
std::optional<std::vector<uint8_t>> readFrame(int fd);  // returns the payload only

#endif
