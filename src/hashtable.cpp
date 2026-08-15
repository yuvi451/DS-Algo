#include "hashtable.h"

#include <cassert>

namespace {
constexpr size_t kInitSize = 4;
constexpr size_t kMaxLoadFactor = 8;
constexpr size_t kRehashWork = 128;
}  // namespace

void HMap::htabInit(HTab &htab, size_t n) {
    assert(n > 0 && ((n - 1) & n) == 0);  // n must be a power of two
    htab.tab.assign(n, nullptr);
    htab.mask = n - 1;
    htab.size = 0;
}

void HMap::htabInsert(HTab &htab, HNode *node) {
    size_t pos = node->hcode & htab.mask;
    node->next = htab.tab[pos];
    htab.tab[pos] = node;
    htab.size++;
}

HNode **HMap::htabLookup(HTab &htab, const HNode *key, EqFn eq) {
    if (htab.tab.empty()) {
        return nullptr;
    }
    size_t pos = key->hcode & htab.mask;
    HNode **from = &htab.tab[pos];
    for (HNode *cur; (cur = *from) != nullptr; from = &cur->next) {
        if (cur->hcode == key->hcode && eq(cur, key)) {
            return from;
        }
    }
    return nullptr;
}

HNode *HMap::htabDetach(HTab &htab, HNode **from) {
    HNode *node = *from;
    *from = node->next;
    htab.size--;
    return node;
}

void HMap::startResizing() {
    assert(older_.tab.empty());
    older_ = std::move(newer_);
    htabInit(newer_, (older_.mask + 1) * 2);
    migratePos_ = 0;
}

void HMap::helpRehashing() {
    size_t nwork = 0;
    while (nwork < kRehashWork && older_.size > 0) {
        HNode **from = &older_.tab[migratePos_];
        if (!*from) {
            migratePos_++;
            continue;
        }
        htabInsert(newer_, htabDetach(older_, from));
        nwork++;
    }
    if (older_.size == 0 && !older_.tab.empty()) {
        older_ = HTab{};
    }
}

HMap::HMap(EqFn eq, DeleteFn deleter) : eq_(eq), deleter_(std::move(deleter)) {}

HMap::~HMap() {
    for (size_t i = 0; i < newer_.tab.size(); i++) {
        for (HNode *node = newer_.tab[i]; node;) {
            HNode *next = node->next;
            if (deleter_) {
                deleter_(node);
            }
            node = next;
        }
    }
    for (size_t i = 0; i < older_.tab.size(); i++) {
        for (HNode *node = older_.tab[i]; node;) {
            HNode *next = node->next;
            if (deleter_) {
                deleter_(node);
            }
            node = next;
        }
    }
}

void HMap::insert(HNode *node) {
    if (newer_.tab.empty()) {
        htabInit(newer_, kInitSize);
    }
    htabInsert(newer_, node);

    if (older_.tab.empty()) {
        size_t threshold = (newer_.mask + 1) * kMaxLoadFactor;
        if (newer_.size >= threshold) {
            startResizing();
        }
    }
    helpRehashing();
}

HNode *HMap::lookup(const HNode *key) const {
    auto *self = const_cast<HMap *>(this);
    HNode **from = htabLookup(self->newer_, key, eq_);
    if (!from) {
        from = htabLookup(self->older_, key, eq_);
    }
    return from ? *from : nullptr;
}

HNode *HMap::pop(const HNode *key) {
    HNode **from = htabLookup(newer_, key, eq_);
    if (from) {
        HNode *node = htabDetach(newer_, from);
        helpRehashing();
        return node;
    }
    from = htabLookup(older_, key, eq_);
    if (from) {
        HNode *node = htabDetach(older_, from);
        helpRehashing();
        return node;
    }
    return nullptr;
}

size_t HMap::size() const {
    return newer_.size + older_.size;
}

uint64_t hashBytes(const uint8_t *data, size_t len) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (size_t i = 0; i < len; i++) {
        h ^= data[i];
        h *= 0x100000001b3ULL;
    }
    return h;
}
