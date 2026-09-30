#ifndef HASHTABLE_H
#define HASHTABLE_H

#include <cstddef>
#include <cstdint>
#include <vector>

// Intrusive node: embed it in your own struct (see Entry in server.cpp).
struct HNode {
    HNode *next = nullptr;
    uint64_t hcode = 0;
};

using EqFn = bool (*)(const HNode *a, const HNode *b);
using DeleteFn = void (*)(HNode *node);

// Chained hashtable that resizes incrementally: when the load factor is hit,
// entries move from the old table to the new one a few at a time on each
// insert/pop, so no single operation pays for the whole resize.
class HMap {
public:
    HMap(EqFn eq, DeleteFn deleter) : eq_(eq), deleter_(deleter) {}
    ~HMap();

    HMap(const HMap &) = delete;
    HMap &operator=(const HMap &) = delete;

    void insert(HNode *node);
    HNode *lookup(const HNode *key) const;
    HNode *pop(const HNode *key);  // caller takes ownership of the result
    size_t size() const { return newer_.size + older_.size; }

private:
    struct HTab {
        std::vector<HNode *> tab;
        size_t mask = 0;
        size_t size = 0;
    };

    static void htabInit(HTab &htab, size_t n);
    static void htabInsert(HTab &htab, HNode *node);
    static HNode **htabLookup(HTab &htab, const HNode *key, EqFn eq);
    static HNode *htabDetach(HTab &htab, HNode **from);

    void startResizing();
    void helpRehashing();

    EqFn eq_;
    DeleteFn deleter_;
    HTab newer_;
    HTab older_;  // non-empty only while a resize is in progress
    size_t migratePos_ = 0;
};

uint64_t hashBytes(const uint8_t *data, size_t len);

#endif
