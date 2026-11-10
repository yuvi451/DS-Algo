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

int main() {
    testSetAndGet();
    testDel();
    cout << "All hashtable tests passed." << endl;
    return 0;
}
