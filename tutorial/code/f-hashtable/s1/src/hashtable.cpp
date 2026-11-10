#include "hashtable.h"

// FNV-1a: a simple, fast hash for strings.
uint64_t hashString(const string &s) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (char c : s) {
        h ^= (unsigned char)c;
        h *= 0x100000001b3ULL;
    }
    return h;
}
