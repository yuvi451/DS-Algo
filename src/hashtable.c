#include <stdlib.h>
#include <assert.h>
#include "hashtable.h"

#define HT_INIT_SIZE 4
#define HT_MAX_LOAD_FACTOR 8
#define HT_REHASH_WORK 128

static void h_init(HTab *htab, size_t n) {
    assert(n > 0 && ((n - 1) & n) == 0); /* n must be a power of two */
    htab->tab = (HNode **)calloc(n, sizeof(HNode *));
    htab->mask = n - 1;
    htab->size = 0;
}

static void h_insert(HTab *htab, HNode *node) {
    size_t pos = node->hcode & htab->mask;
    node->next = htab->tab[pos];
    htab->tab[pos] = node;
    htab->size++;
}

static HNode **h_lookup(HTab *htab, HNode *key, HEqFn eq) {
    if (!htab->tab) {
        return NULL;
    }
    size_t pos = key->hcode & htab->mask;
    HNode **from = &htab->tab[pos];
    for (HNode *cur; (cur = *from) != NULL; from = &cur->next) {
        if (cur->hcode == key->hcode && eq(cur, key)) {
            return from;
        }
    }
    return NULL;
}

static HNode *h_detach(HTab *htab, HNode **from) {
    HNode *node = *from;
    *from = node->next;
    htab->size--;
    return node;
}

static void hm_start_resizing(HMap *map) {
    assert(map->older.tab == NULL);
    map->older = map->newer;
    h_init(&map->newer, (map->older.mask + 1) * 2);
    map->migrate_pos = 0;
}

static void hm_help_rehashing(HMap *map) {
    size_t nwork = 0;
    while (nwork < HT_REHASH_WORK && map->older.size > 0) {
        HNode **from = &map->older.tab[map->migrate_pos];
        if (!*from) {
            map->migrate_pos++;
            continue;
        }
        h_insert(&map->newer, h_detach(&map->older, from));
        nwork++;
    }
    if (map->older.size == 0 && map->older.tab) {
        free(map->older.tab);
        map->older = (HTab){0};
    }
}

void hm_init(HMap *map) {
    *map = (HMap){0};
}

void hm_insert(HMap *map, HNode *node) {
    if (!map->newer.tab) {
        h_init(&map->newer, HT_INIT_SIZE);
    }
    h_insert(&map->newer, node);

    if (!map->older.tab) {
        size_t threshold = (map->newer.mask + 1) * HT_MAX_LOAD_FACTOR;
        if (map->newer.size >= threshold) {
            hm_start_resizing(map);
        }
    }
    hm_help_rehashing(map);
}

HNode *hm_lookup(HMap *map, HNode *key, HEqFn eq) {
    HNode **from = h_lookup(&map->newer, key, eq);
    if (!from) {
        from = h_lookup(&map->older, key, eq);
    }
    return from ? *from : NULL;
}

HNode *hm_pop(HMap *map, HNode *key, HEqFn eq) {
    HNode **from = h_lookup(&map->newer, key, eq);
    if (from) {
        HNode *node = h_detach(&map->newer, from);
        hm_help_rehashing(map);
        return node;
    }
    from = h_lookup(&map->older, key, eq);
    if (from) {
        HNode *node = h_detach(&map->older, from);
        hm_help_rehashing(map);
        return node;
    }
    return NULL;
}

size_t hm_size(const HMap *map) {
    return map->newer.size + map->older.size;
}

void hm_destroy(HMap *map, void (*free_node)(HNode *node)) {
    for (size_t i = 0; map->newer.tab && i <= map->newer.mask; i++) {
        for (HNode *node = map->newer.tab[i]; node;) {
            HNode *next = node->next;
            if (free_node) {
                free_node(node);
            }
            node = next;
        }
    }
    for (size_t i = 0; map->older.tab && i <= map->older.mask; i++) {
        for (HNode *node = map->older.tab[i]; node;) {
            HNode *next = node->next;
            if (free_node) {
                free_node(node);
            }
            node = next;
        }
    }
    free(map->newer.tab);
    free(map->older.tab);
    *map = (HMap){0};
}

uint64_t hash_bytes(const uint8_t *data, size_t len) {
    uint64_t h = 0xcbf29ce484222325ULL; /* FNV offset basis */
    for (size_t i = 0; i < len; i++) {
        h ^= data[i];
        h *= 0x100000001b3ULL; /* FNV prime */
    }
    return h;
}
