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

// Chained hashtable. For now it never grows (that's the next lesson).
struct HashMap {
    Table newer;
    Table older;  // stays empty until the next lesson adds growing

    bool get(const string &key, string &val);  // false if key is missing
    void set(const string &key, const string &val);
    bool del(const string &key);  // false if key was missing
    size_t size();
};

uint64_t hashString(const string &s);
