#include <cassert>
#include <iostream>

#include "../src/hashtable.h"
using namespace std;

void testSetAndGet() {
    HashMap m;
    string val;
    assert(!m.get("name", val));
    m.set("name", "redis");
    assert(m.get("name", val));
    assert(val == "redis");
    m.set("name", "microredis");  // overwrite
    assert(m.get("name", val));
    assert(val == "microredis");
    assert(m.size() == 1);
    cout << "testSetAndGet: OK" << endl;
}

void testDel() {
    HashMap m;
    m.set("a", "1");
    assert(m.del("a"));
    assert(!m.del("a"));
    assert(m.size() == 0);
    string val;
    assert(!m.get("a", val));
    cout << "testDel: OK" << endl;
}

// Enough keys to make the table grow several times. Checks that every key is
// still found while nodes are halfway between the two tables.
void testGrowing() {
    const int N = 5000;
    HashMap m;
    bool sawGrowing = false;
    for (int i = 0; i < N; i++) {
        m.set("key" + to_string(i), "val" + to_string(i));
        if (!m.older.buckets.empty()) sawGrowing = true;
    }
    assert(sawGrowing);
    assert(m.size() == N);

    string val;
    for (int i = 0; i < N; i++) {
        assert(m.get("key" + to_string(i), val));
        assert(val == "val" + to_string(i));
    }
    assert(!m.get("key" + to_string(N), val));

    for (int i = 0; i < N; i += 2) assert(m.del("key" + to_string(i)));
    assert(m.size() == N / 2);
    for (int i = 0; i < N; i++) {
        bool found = m.get("key" + to_string(i), val);
        assert(found == (i % 2 == 1));  // only odd keys remain
    }
    cout << "testGrowing: OK" << endl;
}

int main() {
    testSetAndGet();
    testDel();
    testGrowing();
    cout << "All hashtable tests passed." << endl;
    return 0;
}
