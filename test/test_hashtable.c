#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/hashtable.h"

typedef struct {
    HNode node;
    int key;
    int val;
} TestNode;

static bool test_eq(HNode *a, HNode *b) {
    return ((TestNode *)a)->key == ((TestNode *)b)->key;
}

static TestNode *make_node(int key, int val) {
    TestNode *n = malloc(sizeof(TestNode));
    n->node.next = NULL;
    n->node.hcode = hash_bytes((const uint8_t *)&key, sizeof(key));
    n->key = key;
    n->val = val;
    return n;
}

static TestNode *find(HMap *map, int key) {
    TestNode probe = {0};
    probe.key = key;
    probe.node.hcode = hash_bytes((const uint8_t *)&key, sizeof(key));
    HNode *found = hm_lookup(map, &probe.node, test_eq);
    return found ? (TestNode *)found : NULL;
}

static void free_node_cb(HNode *node) {
    free(node);
}

static void test_insert_and_lookup(void) {
    HMap map;
    hm_init(&map);

    TestNode *n = make_node(42, 100);
    hm_insert(&map, &n->node);

    TestNode *found = find(&map, 42);
    assert(found != NULL);
    assert(found->val == 100);
    assert(find(&map, 99) == NULL);

    hm_destroy(&map, free_node_cb);
    printf("test_insert_and_lookup: OK\n");
}

static void test_delete(void) {
    HMap map;
    hm_init(&map);

    TestNode *n = make_node(7, 77);
    hm_insert(&map, &n->node);
    assert(hm_size(&map) == 1);

    TestNode probe = {0};
    probe.key = 7;
    probe.node.hcode = hash_bytes((const uint8_t *)&probe.key, sizeof(probe.key));
    HNode *popped = hm_pop(&map, &probe.node, test_eq);
    assert(popped != NULL);
    free(popped);

    assert(hm_size(&map) == 0);
    assert(find(&map, 7) == NULL);

    hm_destroy(&map, free_node_cb);
    printf("test_delete: OK\n");
}

static void test_collision_chaining(void) {
    HMap map;
    hm_init(&map);

    /* Force all four nodes into the same bucket by giving them an
       identical hash code, regardless of table size. */
    for (int i = 0; i < 4; i++) {
        TestNode *n = malloc(sizeof(TestNode));
        n->node.next = NULL;
        n->node.hcode = 1;
        n->key = i;
        n->val = i * 10;
        hm_insert(&map, &n->node);
    }
    assert(hm_size(&map) == 4);

    for (int i = 0; i < 4; i++) {
        TestNode probe = {0};
        probe.key = i;
        probe.node.hcode = 1;
        HNode *found = hm_lookup(&map, &probe.node, test_eq);
        assert(found != NULL);
        assert(((TestNode *)found)->val == i * 10);
    }

    hm_destroy(&map, free_node_cb);
    printf("test_collision_chaining: OK\n");
}

#define N_REHASH_KEYS 5000

static void test_progressive_rehash(void) {
    HMap map;
    hm_init(&map);

    for (int i = 0; i < N_REHASH_KEYS; i++) {
        hm_insert(&map, &make_node(i, i)->node);
    }
    assert(hm_size(&map) == N_REHASH_KEYS);

    for (int i = 0; i < N_REHASH_KEYS; i++) {
        TestNode *found = find(&map, i);
        assert(found != NULL);
        assert(found->val == i);
    }
    assert(find(&map, -1) == NULL);
    assert(find(&map, N_REHASH_KEYS) == NULL);

    /* Delete every other key while a rehash may still be migrating in the
       background, then confirm the rest still resolve correctly. */
    for (int i = 0; i < N_REHASH_KEYS; i += 2) {
        TestNode probe = {0};
        probe.key = i;
        probe.node.hcode = hash_bytes((const uint8_t *)&probe.key, sizeof(probe.key));
        HNode *popped = hm_pop(&map, &probe.node, test_eq);
        assert(popped != NULL);
        free(popped);
    }
    assert(hm_size(&map) == N_REHASH_KEYS / 2);

    for (int i = 0; i < N_REHASH_KEYS; i++) {
        TestNode *found = find(&map, i);
        if (i % 2 == 0) {
            assert(found == NULL);
        } else {
            assert(found != NULL);
            assert(found->val == i);
        }
    }

    hm_destroy(&map, free_node_cb);
    printf("test_progressive_rehash: OK\n");
}

int main(void) {
    test_insert_and_lookup();
    test_delete();
    test_collision_chaining();
    test_progressive_rehash();
    printf("All hashtable tests passed.\n");
    return 0;
}
