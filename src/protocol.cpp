#include "protocol.h"

#include <cassert>
#include <cstring>
#include <unistd.h>

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
    uint32_t n = static_cast<uint32_t>(args.size());
    out.append(reinterpret_cast<const uint8_t *>(&n), 4);
    for (const auto &arg : args) {
        uint32_t l = static_cast<uint32_t>(arg.size());
        out.append(reinterpret_cast<const uint8_t *>(&l), 4);
        out.append(arg);
    }
    return out.size() <= K_MAX_MSG;
}

std::optional<std::vector<std::string>> parseRequest(const uint8_t *data, size_t len) {
    if (len < 4) {
        return std::nullopt;
    }
    uint32_t nargs;
    std::memcpy(&nargs, data, 4);
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
        uint32_t l;
        std::memcpy(&l, data + pos, 4);
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
        uint32_t l = static_cast<uint32_t>(data.size());
        out.append(reinterpret_cast<const uint8_t *>(&l), 4);
        out.append(data);
    }
}

std::optional<Response> parseResponse(const uint8_t *data, size_t len) {
    if (len < 1) {
        return std::nullopt;
    }
    ResponseStatus status = static_cast<ResponseStatus>(data[0]);
    if (len == 1) {
        return Response{status, std::string()};
    }
    if (len < 5) {
        return std::nullopt;
    }
    uint32_t l;
    std::memcpy(&l, data + 1, 4);
    if (5 + static_cast<size_t>(l) != len) {
        return std::nullopt;
    }
    return Response{status, std::string(reinterpret_cast<const char *>(data + 5), l)};
}

FrameStatus tryParseFrame(const uint8_t *buf, size_t bufLen, FrameInfo &out) {
    if (bufLen < 4) {
        return FrameStatus::Incomplete;
    }
    uint32_t len;
    std::memcpy(&len, buf, 4);
    if (len > K_MAX_MSG) {
        return FrameStatus::Malformed;
    }
    if (bufLen < 4 + static_cast<size_t>(len)) {
        return FrameStatus::Incomplete;
    }
    out.frameLen = 4 + len;
    out.payloadOff = 4;
    out.payloadLen = len;
    return FrameStatus::Complete;
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

std::optional<Buffer> readFrame(int fd) {
    uint8_t head[4];
    if (!readFull(fd, head, 4)) {
        return std::nullopt;
    }
    uint32_t len;
    std::memcpy(&len, head, 4);
    if (len > K_MAX_MSG) {
        return std::nullopt;
    }

    Buffer out;
    out.append(head, 4);
    if (len > 0) {
        std::vector<uint8_t> tmp(len);
        if (!readFull(fd, tmp.data(), len)) {
            return std::nullopt;
        }
        out.append(tmp.data(), len);
    }
    return out;
}

bool writeFrame(int fd, const uint8_t *payload, size_t len) {
    if (len > K_MAX_MSG) {
        return false;
    }
    uint8_t head[4];
    uint32_t l = static_cast<uint32_t>(len);
    std::memcpy(head, &l, 4);
    if (!writeAll(fd, head, 4)) {
        return false;
    }
    if (len > 0 && !writeAll(fd, payload, len)) {
        return false;
    }
    return true;
}
