#include <cerrno>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <memory>
#include <vector>

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>

#include "hashtable.h"
#include "protocol.h"

class Entry : public HNode {
public:
    std::string key;
    std::string val;
};

static bool entryEq(const HNode *lhs, const HNode *rhs) {
    const auto *le = static_cast<const Entry *>(lhs);
    const auto *re = static_cast<const Entry *>(rhs);
    return le->key == re->key;
}

class KvStore {
public:
    KvStore() : map_(entryEq, [](HNode *n) { delete static_cast<Entry *>(n); }) {}

    std::optional<std::string> get(std::string_view key) const {
        Entry probe;
        probe.key = std::string(key);
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(probe.key.data()), probe.key.size());

        HNode *node = map_.lookup(&probe);
        if (!node) {
            return std::nullopt;
        }
        return static_cast<Entry *>(node)->val;
    }

    void set(std::string_view key, std::string_view val) {
        Entry probe;
        probe.key = std::string(key);
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(probe.key.data()), probe.key.size());

        HNode *node = map_.lookup(&probe);
        if (node) {
            static_cast<Entry *>(node)->val = std::string(val);
            return;
        }
        auto *e = new Entry();
        e->key = std::string(key);
        e->val = std::string(val);
        e->hcode = probe.hcode;
        map_.insert(e);
    }

    bool del(std::string_view key) {
        Entry probe;
        probe.key = std::string(key);
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(probe.key.data()), probe.key.size());

        HNode *node = map_.pop(&probe);
        if (!node) {
            return false;
        }
        delete static_cast<Entry *>(node);
        return true;
    }

private:
    HMap map_;
};

class Conn {
public:
    explicit Conn(int fd) : fd_(fd) {
        int flags = fcntl(fd_, F_GETFL, 0);
        if (flags == -1) {
            perror("fcntl(F_GETFL)");
            exit(1);
        }
        if (fcntl(fd_, F_SETFL, flags | O_NONBLOCK) == -1) {
            perror("fcntl(F_SETFL)");
            exit(1);
        }
    }

    ~Conn() { close(fd_); }

    Conn(const Conn &) = delete;
    Conn &operator=(const Conn &) = delete;

    int fd() const { return fd_; }

    bool wantRead = true;
    bool wantWrite = false;
    bool wantClose = false;
    Buffer incoming;
    Buffer outgoing;

private:
    int fd_;
};

static std::vector<std::unique_ptr<Conn>> g_fd2conn;

static void fd2connPut(int fd, std::unique_ptr<Conn> conn) {
    if (static_cast<size_t>(fd) >= g_fd2conn.size()) {
        g_fd2conn.resize(static_cast<size_t>(fd) + 1);
    }
    g_fd2conn[static_cast<size_t>(fd)] = std::move(conn);
}

static void encodeCommand(KvStore &store, const std::vector<std::string> &args, Buffer &out) {
    if (args.size() == 2 && args[0] == "get") {
        auto val = store.get(args[1]);
        if (!val) {
            encodeResponse(out, ResponseStatus::Nx);
        } else {
            encodeResponse(out, ResponseStatus::Ok, *val);
        }
    } else if (args.size() == 3 && args[0] == "set") {
        store.set(args[1], args[2]);
        encodeResponse(out, ResponseStatus::Ok);
    } else if (args.size() == 2 && args[0] == "del") {
        bool existed = store.del(args[1]);
        encodeResponse(out, existed ? ResponseStatus::Ok : ResponseStatus::Nx);
    } else {
        encodeResponse(out, ResponseStatus::Err);
    }
}

static void doRequest(KvStore &store, const std::vector<std::string> &args, Buffer &out) {
    // Responses are framed just like requests: build the payload into a
    // scratch buffer, then prepend its 4-byte length before appending to
    // the connection's real outgoing buffer.
    Buffer resp;
    encodeCommand(store, args, resp);

    uint32_t len = static_cast<uint32_t>(resp.size());
    out.append(reinterpret_cast<const uint8_t *>(&len), 4);
    out.append(resp.data(), resp.size());
}

static void processBufferedRequests(KvStore &store, Conn &conn) {
    while (true) {
        FrameInfo info{};
        FrameStatus status = tryParseFrame(conn.incoming.data(), conn.incoming.size(), info);
        if (status == FrameStatus::Incomplete) {
            break;
        }
        if (status == FrameStatus::Malformed) {
            conn.wantClose = true;
            return;
        }
        auto args = parseRequest(conn.incoming.data() + info.payloadOff, info.payloadLen);
        if (!args) {
            conn.wantClose = true;
            return;
        }
        doRequest(store, *args, conn.outgoing);
        conn.incoming.consume(info.frameLen);
    }
}

static void handleRead(KvStore &store, Conn &conn) {
    uint8_t tmp[64 * 1024];
    ssize_t rv = read(conn.fd(), tmp, sizeof(tmp));
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv <= 0) {
        conn.wantClose = true;
        return;
    }
    conn.incoming.append(tmp, static_cast<size_t>(rv));
    processBufferedRequests(store, conn);
    conn.wantWrite = conn.outgoing.size() > 0;
}

static void handleWrite(Conn &conn) {
    ssize_t rv = write(conn.fd(), conn.outgoing.data(), conn.outgoing.size());
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv < 0) {
        conn.wantClose = true;
        return;
    }
    conn.outgoing.consume(static_cast<size_t>(rv));
    conn.wantWrite = conn.outgoing.size() > 0;
}

static int makeListener() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket()");
        exit(1);
    }

    int val = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &val, sizeof(val));

    struct sockaddr_in addr {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(fd, reinterpret_cast<struct sockaddr *>(&addr), sizeof(addr)) != 0) {
        perror("bind()");
        exit(1);
    }
    if (listen(fd, SOMAXCONN) != 0) {
        perror("listen()");
        exit(1);
    }

    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
    return fd;
}

static void acceptNewConn(int listenFd) {
    struct sockaddr_in clientAddr {};
    socklen_t addrlen = sizeof(clientAddr);
    int connfd = accept(listenFd, reinterpret_cast<struct sockaddr *>(&clientAddr), &addrlen);
    if (connfd < 0) {
        return;
    }
    fd2connPut(connfd, std::make_unique<Conn>(connfd));
}

int main() {
    signal(SIGPIPE, SIG_IGN);
    KvStore store;

    int listenFd = makeListener();
    fprintf(stderr, "listening on 127.0.0.1:%d\n", SERVER_PORT);

    std::vector<struct pollfd> pollArgs;

    while (true) {
        pollArgs.clear();
        pollArgs.push_back({listenFd, POLLIN, 0});

        for (auto &conn : g_fd2conn) {
            if (!conn) {
                continue;
            }
            struct pollfd pfd {};
            pfd.fd = conn->fd();
            pfd.events = POLLERR;
            if (conn->wantRead) {
                pfd.events |= POLLIN;
            }
            if (conn->wantWrite) {
                pfd.events |= POLLOUT;
            }
            pollArgs.push_back(pfd);
        }

        int rv = poll(pollArgs.data(), static_cast<nfds_t>(pollArgs.size()), -1);
        if (rv < 0 && errno == EINTR) {
            continue;
        }
        if (rv < 0) {
            perror("poll()");
            exit(1);
        }

        if (pollArgs[0].revents & POLLIN) {
            acceptNewConn(listenFd);
        }

        for (size_t i = 1; i < pollArgs.size(); i++) {
            short re = pollArgs[i].revents;
            if (!re) {
                continue;
            }
            int fd = pollArgs[i].fd;
            Conn *conn = g_fd2conn[static_cast<size_t>(fd)].get();
            if (!conn) {
                continue;
            }
            if (re & POLLIN) {
                handleRead(store, *conn);
            }
            if (!conn->wantClose && (re & POLLOUT)) {
                handleWrite(*conn);
            }
            if (conn->wantClose || (re & (POLLERR | POLLHUP))) {
                g_fd2conn[static_cast<size_t>(fd)].reset();
            }
        }
    }

    return 0;
}
