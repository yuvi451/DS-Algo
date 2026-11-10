#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>

#include <arpa/inet.h>
#include <unistd.h>
using namespace std;

void die(const string &what) {
    cerr << what << " failed: " << strerror(errno) << endl;
    exit(1);
}

int makeListener() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) die("socket()");
    int yes = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));

    sockaddr_in addr = {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(1234);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (::bind(fd, (sockaddr *)&addr, sizeof(addr)) != 0) die("bind()");
    if (listen(fd, SOMAXCONN) != 0) die("listen()");
    return fd;
}

void talk(int connFd) {
    char buf[64];
    int n = read(connFd, buf, sizeof(buf));
    if (n < 0) {
        cerr << "read() failed" << endl;
        return;
    }
    cout << "client says: " << string(buf, n) << endl;
    write(connFd, "world", 5);
}

int main() {
    int listenFd = makeListener();
    cout << "listening on 127.0.0.1:1234" << endl;

    while (true) {
        int connFd = accept(listenFd, nullptr, nullptr);
        if (connFd < 0) continue;
        talk(connFd);
        close(connFd);
    }
}
