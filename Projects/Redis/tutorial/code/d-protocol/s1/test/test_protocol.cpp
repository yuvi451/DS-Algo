#include <cassert>
#include <iostream>

#include "../src/protocol.h"
using namespace std;

void testU32Roundtrip() {
    string s;
    appendU32(s, 5);
    assert(s.size() == 4);
    assert(s[0] == 5 && s[1] == 0 && s[2] == 0 && s[3] == 0);  // smallest byte first
    assert(readU32(s, 0) == 5);
    cout << "testU32Roundtrip: OK" << endl;
}

int main() {
    testU32Roundtrip();
    cout << "All protocol tests passed." << endl;
    return 0;
}
