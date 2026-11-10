#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

#include <arpa/inet.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <unistd.h>

#include "hashtable.h"
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

// ---- Key-value store ----

HashMap db;

// Runs one command and returns the response payload.
string runCommand(const vector<string> &args) {
    if (args.size() == 2 && args[0] == "get") {
        string val;
        if (db.get(args[1], val)) return encodeResponse(RES_OK, val);
        return encodeResponse(RES_NX);
    }
    if (args.size() == 3 && args[0] == "set") {
        db.set(args[1], args[2]);
        return encodeResponse(RES_OK);
    }
    if (args.size() == 2 && args[0] == "del") {
        if (db.del(args[1])) return encodeResponse(RES_OK);
        return encodeResponse(RES_NX);
    }
    return encodeResponse(RES_ERR);
}

// ---- Connections ----

struct Conn {
    int fd = -1;
    bool wantWrite = false;  // outgoing has bytes: ask poll() for POLLOUT
    bool wantClose = false;  // the event loop should close this connection
    string incoming;         // bytes read but not handled yet
    string outgoing;         // replies waiting to be written
};

// Handles every complete request in incoming (a client may send several at once).
void handleRequests(Conn *conn) {
    while (true) {
        size_t len = 0;
        FrameResult r = tryParseFrame(conn->incoming, len);
        if (r == FRAME_INCOMPLETE) return;  // wait for more bytes

        vector<string> args;
        if (r == FRAME_TOO_BIG || !parseRequest(conn->incoming.substr(HEADER_LEN, len), args)) {
            conn->wantClose = true;  // garbage: hang up
            return;
        }
        conn->outgoing += makeFrame(runCommand(args));
        conn->incoming.erase(0, HEADER_LEN + len);  // done with this request
    }
}

void handleRead(Conn *conn) {
    char buf[64 * 1024];
    int n = read(conn->fd, buf, sizeof(buf));
    if (n < 0 && errno == EAGAIN) return;  // nothing to read after all
    if (n <= 0) {
        conn->wantClose = true;  // error, or the client hung up (n == 0)
        return;
    }
    conn->incoming.append(buf, n);
    handleRequests(conn);
    conn->wantWrite = !conn->outgoing.empty();
}

void handleWrite(Conn *conn) {
    int n = write(conn->fd, conn->outgoing.data(), conn->outgoing.size());
    if (n < 0 && errno == EAGAIN) return;  // socket is full, try later
    if (n < 0) {
        conn->wantClose = true;
        return;
    }
    conn->outgoing.erase(0, n);  // write() may have sent only part of it
    conn->wantWrite = !conn->outgoing.empty();
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

// ---- Event loop ----

int main() {
    signal(SIGPIPE, SIG_IGN);  // writing to a closed socket: return an error, don't kill us
    int listenFd = makeListener();
    cout << "listening on 127.0.0.1:" << PORT << endl;

    vector<Conn *> conns;  // conns[fd] is the connection on that fd, or nullptr

    while (true) {
        // 1. List every socket we want to hear about.
        vector<pollfd> fds;
        fds.push_back({listenFd, POLLIN, 0});
        for (Conn *conn : conns) {
            if (conn == nullptr) continue;
            short events = POLLIN;
            if (conn->wantWrite) events |= POLLOUT;
            fds.push_back({conn->fd, events, 0});
        }

        // 2. Sleep until at least one of them is ready.
        if (poll(fds.data(), fds.size(), -1) < 0) {
            if (errno == EINTR) continue;  // interrupted by a signal, just retry
            die("poll()");
        }

        // 3. A new client is waiting?
        if (fds[0].revents & POLLIN) {
            int fd = accept(listenFd, nullptr, nullptr);
            if (fd >= 0) {
                setNonBlocking(fd);
                if (fd >= (int)conns.size()) conns.resize(fd + 1, nullptr);
                conns[fd] = new Conn();
                conns[fd]->fd = fd;
            }
        }

        // 4. Serve every client that is ready.
        for (size_t i = 1; i < fds.size(); i++) {
            short ready = fds[i].revents;
            if (ready == 0) continue;
            Conn *conn = conns[fds[i].fd];
            if (ready & POLLIN) handleRead(conn);
            if ((ready & POLLOUT) && !conn->wantClose) handleWrite(conn);
            if (conn->wantClose || (ready & (POLLERR | POLLHUP))) {
                close(conn->fd);
                conns[conn->fd] = nullptr;
                delete conn;
            }
        }
    }
}
