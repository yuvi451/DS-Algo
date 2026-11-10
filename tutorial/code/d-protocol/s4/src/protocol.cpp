#include "protocol.h"

void appendU32(string &out, uint32_t v) {
    out.append((char *)&v, 4);  // look at v as 4 raw bytes and copy them
}

uint32_t readU32(const string &s, size_t pos) {
    uint32_t v;
    s.copy((char *)&v, 4, pos);  // copy 4 bytes from s[pos] into v
    return v;
}

string encodeRequest(const vector<string> &args) {
    string out;
    appendU32(out, args.size());
    for (const string &arg : args) {
        appendU32(out, arg.size());
        out += arg;
    }
    return out;
}

// The bytes come from another program, so check every length before using it.
bool parseRequest(const string &payload, vector<string> &args) {
    if (payload.size() < 4) return false;
    uint32_t nargs = readU32(payload, 0);
    if (nargs > 1024) return false;

    size_t pos = 4;
    for (uint32_t i = 0; i < nargs; i++) {
        if (pos + 4 > payload.size()) return false;
        uint32_t len = readU32(payload, pos);
        pos += 4;
        if (pos + len > payload.size()) return false;
        args.push_back(payload.substr(pos, len));
        pos += len;
    }
    return pos == payload.size();  // no junk left over
}

string encodeResponse(Status status, const string &data) {
    string out;
    out += (char)status;
    if (!data.empty()) {
        appendU32(out, data.size());
        out += data;
    }
    return out;
}

bool parseResponse(const string &payload, Status &status, string &data) {
    if (payload.empty()) return false;
    status = (Status)payload[0];
    data = "";
    if (payload.size() == 1) return true;
    if (payload.size() < 5 || 5 + readU32(payload, 1) != payload.size()) return false;
    data = payload.substr(5);
    return true;
}

string makeFrame(const string &payload) {
    string out;
    appendU32(out, payload.size());
    return out + payload;
}

// Is there a whole frame at the front of buf? Doesn't remove anything.
FrameResult tryParseFrame(const string &buf, size_t &payloadLen) {
    if (buf.size() < HEADER_LEN) return FRAME_INCOMPLETE;
    payloadLen = readU32(buf, 0);
    if (payloadLen > MAX_MSG) return FRAME_TOO_BIG;
    if (buf.size() < HEADER_LEN + payloadLen) return FRAME_INCOMPLETE;
    return FRAME_COMPLETE;
}
