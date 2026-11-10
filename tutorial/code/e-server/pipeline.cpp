// Sends three requests in ONE write(), then reads the three replies.
// A server that assumes "one read() == one request" fails this test.
#include <iostream>
#include <string>
#include <vector>

#include <unistd.h>

#include "../src/protocol.h"
using namespace std;

int main() {
    vector<vector<string>> cmds = {
        {"set", "lang", "c++"},
        {"get", "lang"},
        {"del", "lang"},
    };

    string all;  // every framed request, back to back
    for (const vector<string> &cmd : cmds) {
        all += makeFrame(encodeRequest(cmd));
    }
    cout << "sending " << all.size() << " bytes in one write()" << endl;

    int fd = connectToServer();
    if (fd < 0) {
        cout << "could not connect" << endl;
        return 1;
    }
    write(fd, all.data(), all.size());

    for (int i = 1; i <= 3; i++) {
        string payload;
        if (!readFrame(fd, payload)) {
            cout << "reply " << i << ": failed to read" << endl;
            return 1;
        }
        Status status;
        string data;
        parseResponse(payload, status, data);
        cout << "reply " << i << ": status=" << status << " data=\"" << data << "\"" << endl;
    }
    close(fd);
    return 0;
}
