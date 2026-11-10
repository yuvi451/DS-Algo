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

int main() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) die("socket()");

    sockaddr_in addr = {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(1234);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (connect(fd, (sockaddr *)&addr, sizeof(addr)) != 0) die("connect()");

    write(fd, "hello", 5);

    char buf[64];
    int n = read(fd, buf, sizeof(buf));
    if (n < 0) die("read()");
    cout << "server says: " << string(buf, n) << endl;
    close(fd);
    return 0;
}
