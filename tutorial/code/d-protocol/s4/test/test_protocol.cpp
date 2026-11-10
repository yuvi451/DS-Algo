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

void testResponseRoundtripWithData() {
    string payload = encodeResponse(RES_OK, "bar");
    Status status;
    string data;
    assert(parseResponse(payload, status, data));
    assert(status == RES_OK);
    assert(data == "bar");
    cout << "testResponseRoundtripWithData: OK" << endl;
}

void testResponseRoundtripStatusOnly() {
    string payload = encodeResponse(RES_NX);
    Status status;
    string data;
    assert(parseResponse(payload, status, data));
    assert(status == RES_NX);
    assert(data.empty());
    cout << "testResponseRoundtripStatusOnly: OK" << endl;
}

void testTryParseFrame() {
    string payload = encodeResponse(RES_OK, "hi");
    string framed = makeFrame(payload);

    size_t len = 0;
    assert(tryParseFrame(framed.substr(0, 3), len) == FRAME_INCOMPLETE);
    assert(tryParseFrame(framed.substr(0, framed.size() - 1), len) == FRAME_INCOMPLETE);
    assert(tryParseFrame(framed, len) == FRAME_COMPLETE);
    assert(len == payload.size());
    assert(HEADER_LEN + len == framed.size());
    cout << "testTryParseFrame: OK" << endl;
}

void testTryParseFrameRejectsOversized() {
    string buf;
    appendU32(buf, MAX_MSG + 1);
    size_t len = 0;
    assert(tryParseFrame(buf, len) == FRAME_TOO_BIG);
    cout << "testTryParseFrameRejectsOversized: OK" << endl;
}

int main() {
    testU32Roundtrip();
    testRequestRoundtrip();
    testRequestRejectsTruncated();
    testResponseRoundtripWithData();
    testResponseRoundtripStatusOnly();
    testTryParseFrame();
    testTryParseFrameRejectsOversized();
    cout << "All protocol tests passed." << endl;
    return 0;
}
