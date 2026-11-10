#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

#include <arpa/inet.h>
#include <fcntl.h>
#include <poll.h>
#include <unistd.h>

#include "protocol.h"
using namespace std;

void die(const string &what) {
    cerr << what << " failed: " << strerror(errno) << endl;
    exit(1);
}

// After this, read/write/accept on fd never wait. If they can't do anything
// right now they return -1 with errno == EAGAIN.
void setNonBlocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

int makeListener() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) die("socket()");
    int yes = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));  // allow quick restarts

    sockaddr_in addr = {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);  // 127.0.0.1
    // "::bind" = the operating system's bind(). Plain "bind" would mean
    // std::bind, an unrelated function pulled in by "using namespace std".
    if (::bind(fd, (sockaddr *)&addr, sizeof(addr)) != 0) die("bind()");
    if (listen(fd, SOMAXCONN) != 0) die("listen()");
    setNonBlocking(fd);
    return fd;
}

int main() {
    int listenFd = makeListener();
    cout << "listening on 127.0.0.1:" << PORT << endl;

    while (true) {
        vector<pollfd> fds;
        fds.push_back({listenFd, POLLIN, 0});

        if (poll(fds.data(), fds.size(), -1) < 0) {
            if (errno == EINTR) continue;  // interrupted by a signal, just retry
            die("poll()");
        }

        if (fds[0].revents & POLLIN) {
            int fd = accept(listenFd, nullptr, nullptr);
            if (fd >= 0) {
                cout << "accepted a connection on fd " << fd << endl;
                close(fd);
            }
        }
    }
}
