#include "hashtable.h"

#include <cassert>

namespace {
constexpr size_t kInitSize = 4;
constexpr size_t kMaxLoadFactor = 8;
constexpr size_t kRehashWork = 128;  // entries migrated per insert/pop
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

// Returns the slot pointing at the matching node, so the caller can unlink it.
HNode **HMap::htabLookup(HTab &htab, const HNode *key, EqFn eq) {
    if (htab.tab.empty()) {
        return nullptr;
    }
    HNode **from = &htab.tab[key->hcode & htab.mask];
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

HMap::~HMap() {
    for (HTab *htab : {&newer_, &older_}) {
        for (HNode *node : htab->tab) {
            while (node) {
                HNode *next = node->next;
                deleter_(node);
                node = next;
            }
        }
    }
}

void HMap::insert(HNode *node) {
    if (newer_.tab.empty()) {
        htabInit(newer_, kInitSize);
    }
    htabInsert(newer_, node);

    bool resizing = !older_.tab.empty();
    if (!resizing && newer_.size >= (newer_.mask + 1) * kMaxLoadFactor) {
        startResizing();
    }
    helpRehashing();
}

HNode *HMap::lookup(const HNode *key) const {
    // htabLookup hands out a mutable slot for pop(); here we only read it.
    auto *self = const_cast<HMap *>(this);
    for (HTab *htab : {&self->newer_, &self->older_}) {
        if (HNode **from = htabLookup(*htab, key, eq_)) {
            return *from;
        }
    }
    return nullptr;
}

HNode *HMap::pop(const HNode *key) {
    for (HTab *htab : {&newer_, &older_}) {
        if (HNode **from = htabLookup(*htab, key, eq_)) {
            HNode *node = htabDetach(*htab, from);
            helpRehashing();
            return node;
        }
    }
    return nullptr;
}

// FNV-1a
uint64_t hashBytes(const uint8_t *data, size_t len) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (size_t i = 0; i < len; i++) {
        h ^= data[i];
        h *= 0x100000001b3ULL;
    }
    return h;
}
