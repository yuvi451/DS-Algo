#include <cassert>
#include <cstdio>

#include "../src/hashtable.h"

struct TestNode : HNode {
    int key = 0;
    int val = 0;
};

static bool testEq(const HNode *a, const HNode *b) {
    return static_cast<const TestNode *>(a)->key == static_cast<const TestNode *>(b)->key;
}

static void deleteTestNode(HNode *node) {
    delete static_cast<TestNode *>(node);
}

static uint64_t hashInt(int key) {
    return hashBytes(reinterpret_cast<const uint8_t *>(&key), sizeof(key));
}

static TestNode *makeNode(int key, int val, uint64_t hcode) {
    auto *node = new TestNode();
    node->key = key;
    node->val = val;
    node->hcode = hcode;
    return node;
}

static TestNode *find(const HMap &map, int key, uint64_t hcode) {
    TestNode probe;
    probe.key = key;
    probe.hcode = hcode;
    return static_cast<TestNode *>(map.lookup(&probe));
}

static TestNode *find(const HMap &map, int key) {
    return find(map, key, hashInt(key));
}

static bool popAndDelete(HMap &map, int key) {
    TestNode probe;
    probe.key = key;
    probe.hcode = hashInt(key);
    HNode *popped = map.pop(&probe);
    if (!popped) {
        return false;
    }
    deleteTestNode(popped);
    return true;
}

static void testInsertAndLookup() {
    HMap map(testEq, deleteTestNode);
    map.insert(makeNode(42, 100, hashInt(42)));

    assert(find(map, 42) != nullptr);
    assert(find(map, 42)->val == 100);
    assert(find(map, 99) == nullptr);
    printf("testInsertAndLookup: OK\n");
}

static void testDelete() {
    HMap map(testEq, deleteTestNode);
    map.insert(makeNode(7, 77, hashInt(7)));
    assert(map.size() == 1);

    assert(popAndDelete(map, 7));
    assert(!popAndDelete(map, 7));
    assert(map.size() == 0);
    assert(find(map, 7) == nullptr);
    printf("testDelete: OK\n");
}

static void testCollisionChaining() {
    HMap map(testEq, deleteTestNode);
    for (int i = 0; i < 4; i++) {
        map.insert(makeNode(i, i * 10, 1));  // same hcode: all land in one bucket
    }
    assert(map.size() == 4);

    for (int i = 0; i < 4; i++) {
        TestNode *found = find(map, i, 1);
        assert(found != nullptr);
        assert(found->val == i * 10);
    }
    printf("testCollisionChaining: OK\n");
}

// Enough keys to trigger several resizes, with deletes mid-migration.
static void testProgressiveRehash() {
    constexpr int kKeys = 5000;
    HMap map(testEq, deleteTestNode);

    for (int i = 0; i < kKeys; i++) {
        map.insert(makeNode(i, i, hashInt(i)));
    }
    assert(map.size() == kKeys);
    for (int i = 0; i < kKeys; i++) {
        assert(find(map, i) != nullptr);
        assert(find(map, i)->val == i);
    }
    assert(find(map, -1) == nullptr);
    assert(find(map, kKeys) == nullptr);

    for (int i = 0; i < kKeys; i += 2) {
        assert(popAndDelete(map, i));
    }
    assert(map.size() == kKeys / 2);
    for (int i = 0; i < kKeys; i++) {
        assert((find(map, i) == nullptr) == (i % 2 == 0));
    }
    printf("testProgressiveRehash: OK\n");
}

int main() {
    testInsertAndLookup();
    testDelete();
    testCollisionChaining();
    testProgressiveRehash();
    printf("All hashtable tests passed.\n");
    return 0;
}
