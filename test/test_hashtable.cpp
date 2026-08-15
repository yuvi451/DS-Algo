#include <cassert>
#include <cstdio>
#include <cstdlib>
#include "../src/hashtable.h"

struct TestNode : public HNode {
    int key;
    int val;
};

static bool testEq(const HNode *a, const HNode *b) {
    return static_cast<const TestNode *>(a)->key == static_cast<const TestNode *>(b)->key;
}

static void deleteTestNode(HNode *n) {
    delete static_cast<TestNode *>(n);
}

static TestNode *makeNode(int key, int val) {
    auto *n = new TestNode();
    n->key = key;
    n->val = val;
    n->hcode = hashBytes(reinterpret_cast<const uint8_t *>(&key), sizeof(key));
    return n;
}

static TestNode *find(HMap &map, int key) {
    TestNode probe{};
    probe.key = key;
    probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(&key), sizeof(key));
    HNode *found = map.lookup(&probe);
    return found ? static_cast<TestNode *>(found) : nullptr;
}

static void testInsertAndLookup() {
    HMap map(testEq, deleteTestNode);

    TestNode *n = makeNode(42, 100);
    map.insert(n);

    TestNode *found = find(map, 42);
    assert(found != nullptr);
    assert(found->val == 100);
    assert(find(map, 99) == nullptr);

    printf("testInsertAndLookup: OK\n");
}

static void testDelete() {
    HMap map(testEq, deleteTestNode);

    TestNode *n = makeNode(7, 77);
    map.insert(n);
    assert(map.size() == 1);

    TestNode probe{};
    probe.key = 7;
    probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(&probe.key), sizeof(probe.key));
    HNode *popped = map.pop(&probe);
    assert(popped != nullptr);
    delete static_cast<TestNode *>(popped);

    assert(map.size() == 0);
    assert(find(map, 7) == nullptr);

    printf("testDelete: OK\n");
}

static void testCollisionChaining() {
    HMap map(testEq, deleteTestNode);

    for (int i = 0; i < 4; i++) {
        auto *n = new TestNode();
        n->key = i;
        n->val = i * 10;
        n->hcode = 1;  // force all four into the same bucket
        map.insert(n);
    }
    assert(map.size() == 4);

    for (int i = 0; i < 4; i++) {
        TestNode probe{};
        probe.key = i;
        probe.hcode = 1;
        HNode *found = map.lookup(&probe);
        assert(found != nullptr);
        assert(static_cast<TestNode *>(found)->val == i * 10);
    }

    printf("testCollisionChaining: OK\n");
}

static constexpr int kRehashKeys = 5000;

static void testProgressiveRehash() {
    HMap map(testEq, deleteTestNode);

    for (int i = 0; i < kRehashKeys; i++) {
        map.insert(makeNode(i, i));
    }
    assert(map.size() == static_cast<size_t>(kRehashKeys));

    for (int i = 0; i < kRehashKeys; i++) {
        TestNode *found = find(map, i);
        assert(found != nullptr);
        assert(found->val == i);
    }
    assert(find(map, -1) == nullptr);
    assert(find(map, kRehashKeys) == nullptr);

    for (int i = 0; i < kRehashKeys; i += 2) {
        TestNode probe{};
        probe.key = i;
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(&probe.key), sizeof(probe.key));
        HNode *popped = map.pop(&probe);
        assert(popped != nullptr);
        delete static_cast<TestNode *>(popped);
    }
    assert(map.size() == static_cast<size_t>(kRehashKeys / 2));

    for (int i = 0; i < kRehashKeys; i++) {
        TestNode *found = find(map, i);
        if (i % 2 == 0) {
            assert(found == nullptr);
        } else {
            assert(found != nullptr);
            assert(found->val == i);
        }
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
