#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

#include <unistd.h>

#include "protocol.h"

int main(int argc, char **argv) {
    if (argc < 2) {
        std::cerr << "usage: " << argv[0] << " <cmd> [args...]\n";
        return 1;
    }

    Buffer request;
    if (!encodeRequest(request, std::vector<std::string>(argv + 1, argv + argc))) {
        std::cerr << "request too large\n";
        return 1;
    }

    int fd = connectToServer();
    if (fd < 0) {
        perror("connect()");
        return 1;
    }
    if (!writeFrame(fd, request)) {
        std::cerr << "failed to send request\n";
        return 1;
    }
    auto payload = readFrame(fd);
    close(fd);
    if (!payload) {
        std::cerr << "failed to read response\n";
        return 1;
    }

    auto response = parseResponse(payload->data(), payload->size());
    if (!response) {
        std::cerr << "bad response\n";
        return 1;
    }

    switch (response->status) {
    case ResponseStatus::Ok:
        std::cout << (response->data.empty() ? "OK" : response->data) << "\n";
        break;
    case ResponseStatus::Nx:
        std::cout << "(nil)\n";
        break;
    case ResponseStatus::Err:
        std::cout << "(error) unknown command or wrong number of arguments\n";
        break;
    }
    return 0;
}
