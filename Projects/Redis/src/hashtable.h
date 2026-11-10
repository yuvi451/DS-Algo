#pragma once

#include <cstdint>
#include <string>
#include <vector>
using namespace std;

// One key-value pair. Pairs that land in the same bucket form a linked list.
struct Node {
    string key;
    string val;
    uint64_t hash;
    Node *next;
};

// An array of buckets. Its size is always a power of two, so the bucket for
// a hash is (hash & mask), which is the same as hash % size but faster.
struct Table {
    vector<Node *> buckets;
    size_t mask = 0;
    size_t size = 0;  // number of nodes in this table
};

// Chained hashtable that grows a little at a time, like Redis's dict.
// When it gets too full, the current table becomes `older`, a new table twice
// the size becomes `newer`, and every set/del moves a few nodes across.
// So no single call ever has to move everything at once.
struct HashMap {
    Table newer;
    Table older;         // only non-empty while nodes are being moved
    size_t movePos = 0;  // next bucket of `older` to move

    bool get(const string &key, string &val);  // false if key is missing
    void set(const string &key, const string &val);
    bool del(const string &key);  // false if key was missing
    size_t size();
    void moveSomeNodes();
};

uint64_t hashString(const string &s);
