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

void testRequestRoundtrip() {
    string payload = encodeRequest({"set", "foo", "bar"});
    vector<string> args;
    assert(parseRequest(payload, args));
    assert(args.size() == 3);
    assert(args[0] == "set" && args[1] == "foo" && args[2] == "bar");
    cout << "testRequestRoundtrip: OK" << endl;
}

void testRequestRejectsTruncated() {
    string bad;
    appendU32(bad, 5);  // claims 5 args, provides none
    vector<string> args;
    assert(!parseRequest(bad, args));
    cout << "testRequestRejectsTruncated: OK" << endl;
}

int main() {
    testU32Roundtrip();
    testRequestRoundtrip();
    testRequestRejectsTruncated();
    cout << "All protocol tests passed." << endl;
    return 0;
}
