#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include "protocol.h"

static int connectToServer() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket()");
        exit(1);
    }

    struct sockaddr_in addr {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    if (connect(fd, reinterpret_cast<struct sockaddr *>(&addr), sizeof(addr)) != 0) {
        perror("connect()");
        exit(1);
    }
    return fd;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        std::cerr << "usage: " << argv[0] << " <cmd> [args...]\n";
        return 1;
    }

    std::vector<std::string> args(argv + 1, argv + argc);

    Buffer req;
    if (!encodeRequest(req, args)) {
        std::cerr << "request too large\n";
        return 1;
    }

    int fd = connectToServer();
    if (!writeFrame(fd, req.data(), req.size())) {
        std::cerr << "write_frame failed\n";
        return 1;
    }

    auto resp = readFrame(fd);
    if (!resp) {
        std::cerr << "read_frame failed\n";
        return 1;
    }

    auto parsed = parseResponse(resp->data() + 4, resp->size() - 4);
    if (!parsed) {
        std::cerr << "bad response\n";
        return 1;
    }

    switch (parsed->status) {
    case ResponseStatus::Ok:
        if (!parsed->data.empty()) {
            std::cout << parsed->data << "\n";
        } else {
            std::cout << "OK\n";
        }
        break;
    case ResponseStatus::Nx:
        std::cout << "(nil)\n";
        break;
    case ResponseStatus::Err:
        std::cout << "(error) unknown command or wrong number of arguments\n";
        break;
    }

    close(fd);
    return 0;
}
