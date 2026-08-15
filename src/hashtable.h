#ifndef HASHTABLE_H
#define HASHTABLE_H

#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>

struct HNode {
    HNode *next = nullptr;
    uint64_t hcode = 0;
};

using EqFn = bool (*)(const HNode *a, const HNode *b);
using DeleteFn = std::function<void(HNode *)>;

class HMap {
public:
    HMap(EqFn eq, DeleteFn deleter);
    ~HMap();

    HMap(const HMap &) = delete;
    HMap &operator=(const HMap &) = delete;

    void insert(HNode *node);
    HNode *lookup(const HNode *key) const;
    HNode *pop(const HNode *key);
    size_t size() const;

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
    HTab older_;
    size_t migratePos_ = 0;
};

uint64_t hashBytes(const uint8_t *data, size_t len);

#endif
