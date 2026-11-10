#include <iostream>
#include <string>
#include <vector>

#include <unistd.h>

#include "protocol.h"
using namespace std;

int main(int argc, char **argv) {
    if (argc < 2) {
        cerr << "usage: " << argv[0] << " <cmd> [args...]" << endl;
        return 1;
    }

    // argv[0] is the program name; the command is argv[1] onwards.
    vector<string> args;
    for (int i = 1; i < argc; i++) args.push_back(argv[i]);

    string request = encodeRequest(args);
    if (request.size() > MAX_MSG) {
        cerr << "request too large" << endl;
        return 1;
    }

    int fd = connectToServer();
    if (fd < 0) {
        cerr << "could not connect to the server (is it running?)" << endl;
        return 1;
    }
    string reply;
    if (!writeFrame(fd, request) || !readFrame(fd, reply)) {
        cerr << "lost connection to the server" << endl;
        return 1;
    }
    close(fd);

    Status status;
    string data;
    if (!parseResponse(reply, status, data)) {
        cerr << "bad response" << endl;
        return 1;
    }

    if (status == RES_OK) {
        cout << (data.empty() ? "OK" : data) << endl;
    } else if (status == RES_NX) {
        cout << "(nil)" << endl;
    } else {
        cout << "(error) unknown command or wrong number of arguments" << endl;
    }
    return 0;
}
