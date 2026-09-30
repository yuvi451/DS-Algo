#include "protocol.h"

#include <cassert>
#include <cstring>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <unistd.h>

namespace {

void appendU32(Buffer &out, uint32_t v) {
    out.append(reinterpret_cast<const uint8_t *>(&v), 4);
}

uint32_t readU32(const uint8_t *data) {
    uint32_t v;
    std::memcpy(&v, data, 4);
    return v;
}

bool readFull(int fd, uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = read(fd, buf, n);
        if (rv <= 0) {
            return false;
        }
        n -= static_cast<size_t>(rv);
        buf += rv;
    }
    return true;
}

bool writeAll(int fd, const uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = write(fd, buf, n);
        if (rv <= 0) {
            return false;
        }
        n -= static_cast<size_t>(rv);
        buf += rv;
    }
    return true;
}

}  // namespace

void Buffer::append(const uint8_t *data, size_t len) {
    buf_.insert(buf_.end(), data, data + len);
}

void Buffer::append(std::string_view s) {
    append(reinterpret_cast<const uint8_t *>(s.data()), s.size());
}

void Buffer::consume(size_t n) {
    assert(n <= buf_.size());
    buf_.erase(buf_.begin(), buf_.begin() + static_cast<long>(n));
}

bool encodeRequest(Buffer &out, const std::vector<std::string> &args) {
    appendU32(out, static_cast<uint32_t>(args.size()));
    for (const auto &arg : args) {
        appendU32(out, static_cast<uint32_t>(arg.size()));
        out.append(arg);
    }
    return out.size() <= kMaxMsg;
}

std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len) {
    if (len < 4) {
        return std::nullopt;
    }
    uint32_t nargs = readU32(data);
    if (nargs > 1024) {
        return std::nullopt;
    }

    size_t pos = 4;
    std::vector<std::string> args;
    args.reserve(nargs);
    for (uint32_t i = 0; i < nargs; i++) {
        if (pos + 4 > len) {
            return std::nullopt;
        }
        uint32_t l = readU32(data + pos);
        pos += 4;
        if (pos + l > len) {
            return std::nullopt;
        }
        args.emplace_back(reinterpret_cast<const char *>(data + pos), l);
        pos += l;
    }
    if (pos != len) {
        return std::nullopt;
    }
    return args;
}

void encodeResponse(Buffer &out, ResponseStatus status, std::string_view data) {
    uint8_t s = static_cast<uint8_t>(status);
    out.append(&s, 1);
    if (!data.empty()) {
        appendU32(out, static_cast<uint32_t>(data.size()));
        out.append(data);
    }
}

std::optional<Response> parseResponse(const uint8_t *data, size_t len) {
    if (len < 1) {
        return std::nullopt;
    }
    auto status = static_cast<ResponseStatus>(data[0]);
    if (len == 1) {
        return Response{status, std::string()};
    }
    if (len < 5 || 5 + static_cast<size_t>(readU32(data + 1)) != len) {
        return std::nullopt;
    }
    return Response{status, std::string(reinterpret_cast<const char *>(data + 5), len - 5)};
}

void appendFrame(Buffer &out, const Buffer &payload) {
    appendU32(out, static_cast<uint32_t>(payload.size()));
    out.append(payload.data(), payload.size());
}

FrameStatus tryParseFrame(const uint8_t *buf, size_t len, size_t &payloadLen) {
    if (len < kHeaderLen) {
        return FrameStatus::Incomplete;
    }
    payloadLen = readU32(buf);
    if (payloadLen > kMaxMsg) {
        return FrameStatus::Malformed;
    }
    if (len < kHeaderLen + payloadLen) {
        return FrameStatus::Incomplete;
    }
    return FrameStatus::Complete;
}

int connectToServer() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        return -1;
    }
    int one = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(kServerPort);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (connect(fd, reinterpret_cast<sockaddr *>(&addr), sizeof(addr)) != 0) {
        close(fd);
        return -1;
    }
    return fd;
}

bool writeFrame(int fd, const Buffer &payload) {
    if (payload.size() > kMaxMsg) {
        return false;
    }
    Buffer frame;
    appendFrame(frame, payload);
    return writeAll(fd, frame.data(), frame.size());
}

std::optional<std::vector<uint8_t>> readFrame(int fd) {
    uint8_t header[kHeaderLen];
    if (!readFull(fd, header, kHeaderLen)) {
        return std::nullopt;
    }
    uint32_t len = readU32(header);
    if (len > kMaxMsg) {
        return std::nullopt;
    }
    std::vector<uint8_t> payload(len);
    if (!readFull(fd, payload.data(), len)) {
        return std::nullopt;
    }
    return payload;
}
