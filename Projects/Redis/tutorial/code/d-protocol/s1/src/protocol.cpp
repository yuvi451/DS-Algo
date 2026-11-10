#include "protocol.h"

void appendU32(string &out, uint32_t v) {
    out.append((char *)&v, 4);  // look at v as 4 raw bytes and copy them
}

uint32_t readU32(const string &s, size_t pos) {
    uint32_t v;
    s.copy((char *)&v, 4, pos);  // copy 4 bytes from s[pos] into v
    return v;
}
