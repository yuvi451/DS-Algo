#include "hashtable.h"

const size_t INIT_SIZE = 4;        // buckets in a brand new table

// FNV-1a: a simple, fast hash for strings.
uint64_t hashString(const string &s) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (char c : s) {
        h ^= (unsigned char)c;
        h *= 0x100000001b3ULL;
    }
    return h;
}

void initTable(Table &t, size_t n) {
    t.buckets.assign(n, nullptr);  // n empty buckets
    t.mask = n - 1;
    t.size = 0;
}

// Push node onto the front of its bucket's list.
void addNode(Table &t, Node *node) {
    size_t i = node->hash & t.mask;
    node->next = t.buckets[i];
    t.buckets[i] = node;
    t.size++;
}

Node *findNode(Table &t, const string &key, uint64_t hash) {
    if (t.buckets.empty()) return nullptr;
    for (Node *n = t.buckets[hash & t.mask]; n != nullptr; n = n->next) {
        if (n->hash == hash && n->key == key) return n;
    }
    return nullptr;
}

// Unlinks the node with this key from t and returns it, or nullptr.
Node *removeNode(Table &t, const string &key, uint64_t hash) {
    if (t.buckets.empty()) return nullptr;
    size_t i = hash & t.mask;
    Node *prev = nullptr;
    Node *n = t.buckets[i];
    while (n != nullptr) {
        if (n->hash == hash && n->key == key) {
            if (prev == nullptr) {
                t.buckets[i] = n->next;  // it was the first node
            } else {
                prev->next = n->next;
            }
            t.size--;
            return n;
        }
        prev = n;
        n = n->next;
    }
    return nullptr;
}

bool HashMap::get(const string &key, string &val) {
    uint64_t hash = hashString(key);
    Node *n = findNode(newer, key, hash);
    if (n == nullptr) n = findNode(older, key, hash);
    if (n == nullptr) return false;
    val = n->val;
    return true;
}

void HashMap::set(const string &key, const string &val) {
    uint64_t hash = hashString(key);
    Node *n = findNode(newer, key, hash);
    if (n == nullptr) n = findNode(older, key, hash);
    if (n != nullptr) {
        n->val = val;  // key exists: overwrite
        return;
    }

    if (newer.buckets.empty()) initTable(newer, INIT_SIZE);
    addNode(newer, new Node{key, val, hash, nullptr});
}

bool HashMap::del(const string &key) {
    uint64_t hash = hashString(key);
    Node *n = removeNode(newer, key, hash);
    if (n == nullptr) n = removeNode(older, key, hash);
    if (n == nullptr) return false;
    delete n;
    return true;
}

size_t HashMap::size() {
    return newer.size + older.size;
}
