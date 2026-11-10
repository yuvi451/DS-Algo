#include <cerrno>
#include <cstring>
#include <iostream>
#include <string>

#include <fcntl.h>
#include <unistd.h>
using namespace std;

int main() {
    // fd 1 is stdout. write() sends raw bytes to it, no cout involved.
    write(1, "hello via write()\n", 18);

    // Opening a file gives us the lowest free fd: 0, 1, 2 are taken, so 3.
    int fd = open("notes.txt", O_CREAT | O_WRONLY | O_TRUNC, 0644);
    cout << "notes.txt got fd " << fd << endl;
    write(fd, "abc", 3);
    close(fd);

    // Read it back. read() returns how many bytes it actually got.
    fd = open("notes.txt", O_RDONLY);
    char buf[100];
    int n = read(fd, buf, sizeof(buf));
    cout << "read returned " << n << ": " << string(buf, n) << endl;
    n = read(fd, buf, sizeof(buf));
    cout << "read again returned " << n << " (0 means end of file)" << endl;
    close(fd);

    // Failing calls return -1 and set errno. strerror() turns it into text.
    if (open("does/not/exist.txt", O_RDONLY) < 0) {
        cout << "errno is " << errno << ": " << strerror(errno) << endl;
    }
    return 0;
}
