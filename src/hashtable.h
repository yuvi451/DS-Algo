#ifndef HASHTABLE_H
#define HASHTABLE_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct HNode {
    struct HNode *next;
    uint64_t hcode;
} HNode;

typedef struct {
    HNode **tab;
    size_t mask;
    size_t size;
} HTab;

typedef struct {
    HTab newer;
    HTab older;
    size_t migrate_pos;
} HMap;

typedef bool (*HEqFn)(HNode *node, HNode *key);

void hm_init(HMap *map);
void hm_insert(HMap *map, HNode *node);
HNode *hm_lookup(HMap *map, HNode *key, HEqFn eq);
HNode *hm_pop(HMap *map, HNode *key, HEqFn eq);
size_t hm_size(const HMap *map);
void hm_destroy(HMap *map, void (*free_node)(HNode *node));

uint64_t hash_bytes(const uint8_t *data, size_t len);

#endif
