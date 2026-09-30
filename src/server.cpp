#include <cerrno>
#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>

#include "hashtable.h"
#include "protocol.h"

[[noreturn]] static void die(const char *msg) {
    perror(msg);
    exit(1);
}

static void setNonBlocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1 || fcntl(fd, F_SETFL, flags | O_NONBLOCK) == -1) {
        die("fcntl()");
    }
}

// ---- Key-value store ----

struct Entry : HNode {
    std::string key;
    std::string val;
};

static bool entryEq(const HNode *lhs, const HNode *rhs) {
    return static_cast<const Entry *>(lhs)->key == static_cast<const Entry *>(rhs)->key;
}

static void entryDelete(HNode *node) {
    delete static_cast<Entry *>(node);
}

class KvStore {
public:
    std::optional<std::string> get(std::string_view key) const {
        Entry probe = makeProbe(key);
        HNode *node = map_.lookup(&probe);
        if (!node) {
            return std::nullopt;
        }
        return static_cast<Entry *>(node)->val;
    }

    void set(std::string_view key, std::string_view val) {
        Entry probe = makeProbe(key);
        if (HNode *node = map_.lookup(&probe)) {
            static_cast<Entry *>(node)->val = val;
            return;
        }
        auto *entry = new Entry(std::move(probe));
        entry->val = val;
        map_.insert(entry);
    }

    bool del(std::string_view key) {
        Entry probe = makeProbe(key);
        HNode *node = map_.pop(&probe);
        if (!node) {
            return false;
        }
        entryDelete(node);
        return true;
    }

private:
    static Entry makeProbe(std::string_view key) {
        Entry probe;
        probe.key = key;
        probe.hcode = hashBytes(reinterpret_cast<const uint8_t *>(key.data()), key.size());
        return probe;
    }

    HMap map_{entryEq, entryDelete};
};

static void runCommand(KvStore &store, const std::vector<std::string> &args, Buffer &out) {
    if (args.size() == 2 && args[0] == "get") {
        auto val = store.get(args[1]);
        if (val) {
            encodeResponse(out, ResponseStatus::Ok, *val);
        } else {
            encodeResponse(out, ResponseStatus::Nx);
        }
    } else if (args.size() == 3 && args[0] == "set") {
        store.set(args[1], args[2]);
        encodeResponse(out, ResponseStatus::Ok);
    } else if (args.size() == 2 && args[0] == "del") {
        encodeResponse(out, store.del(args[1]) ? ResponseStatus::Ok : ResponseStatus::Nx);
    } else {
        encodeResponse(out, ResponseStatus::Err);
    }
}

// ---- Connections ----

struct Conn {
    explicit Conn(int fd) : fd(fd) { setNonBlocking(fd); }
    ~Conn() { close(fd); }

    Conn(const Conn &) = delete;
    Conn &operator=(const Conn &) = delete;

    const int fd;
    bool wantWrite = false;
    bool wantClose = false;
    Buffer incoming;
    Buffer outgoing;
};

// Handles every complete request in the buffer (clients may pipeline).
static void handleRequests(KvStore &store, Conn &conn) {
    while (true) {
        size_t payloadLen = 0;
        FrameStatus status = tryParseFrame(conn.incoming.data(), conn.incoming.size(), payloadLen);
        if (status == FrameStatus::Incomplete) {
            return;
        }
        std::optional<std::vector<std::string>> args;
        if (status == FrameStatus::Complete) {
            args = parseRequest(conn.incoming.data() + kHeaderLen, payloadLen);
        }
        if (!args) {
            conn.wantClose = true;
            return;
        }

        Buffer response;
        runCommand(store, *args, response);
        appendFrame(conn.outgoing, response);
        conn.incoming.consume(kHeaderLen + payloadLen);
    }
}

static void handleRead(KvStore &store, Conn &conn) {
    uint8_t buf[64 * 1024];
    ssize_t rv = read(conn.fd, buf, sizeof(buf));
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv <= 0) {
        conn.wantClose = true;
        return;
    }
    conn.incoming.append(buf, static_cast<size_t>(rv));
    handleRequests(store, conn);
    conn.wantWrite = conn.outgoing.size() > 0;
}

static void handleWrite(Conn &conn) {
    ssize_t rv = write(conn.fd, conn.outgoing.data(), conn.outgoing.size());
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
        die("socket()");
    }
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(kServerPort);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(fd, reinterpret_cast<sockaddr *>(&addr), sizeof(addr)) != 0) {
        die("bind()");
    }
    if (listen(fd, SOMAXCONN) != 0) {
        die("listen()");
    }
    setNonBlocking(fd);
    return fd;
}

// ---- Event loop ----

int main() {
    signal(SIGPIPE, SIG_IGN);
    KvStore store;
    int listenFd = makeListener();
    fprintf(stderr, "listening on 127.0.0.1:%d\n", kServerPort);

    std::vector<std::unique_ptr<Conn>> conns;  // indexed by fd
    std::vector<pollfd> pollArgs;

    while (true) {
        pollArgs.clear();
        pollArgs.push_back({listenFd, POLLIN, 0});
        for (const auto &conn : conns) {
            if (conn) {
                short events = POLLIN | (conn->wantWrite ? POLLOUT : 0);
                pollArgs.push_back({conn->fd, events, 0});
            }
        }

        if (poll(pollArgs.data(), static_cast<nfds_t>(pollArgs.size()), -1) < 0) {
            if (errno == EINTR) {
                continue;
            }
            die("poll()");
        }

        if (pollArgs[0].revents & POLLIN) {
            int fd = accept(listenFd, nullptr, nullptr);
            if (fd >= 0) {
                if (static_cast<size_t>(fd) >= conns.size()) {
                    conns.resize(static_cast<size_t>(fd) + 1);
                }
                conns[static_cast<size_t>(fd)] = std::make_unique<Conn>(fd);
            }
        }

        for (size_t i = 1; i < pollArgs.size(); i++) {
            short revents = pollArgs[i].revents;
            auto &conn = conns[static_cast<size_t>(pollArgs[i].fd)];
            if (!revents || !conn) {
                continue;
            }
            if (revents & POLLIN) {
                handleRead(store, *conn);
            }
            if (!conn->wantClose && (revents & POLLOUT)) {
                handleWrite(*conn);
            }
            if (conn->wantClose || (revents & (POLLERR | POLLHUP))) {
                conn.reset();
            }
        }
    }
}
