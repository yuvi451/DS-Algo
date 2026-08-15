#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include "hashtable.h"
#include "protocol.h"

typedef struct Entry {
    HNode node;
    char *key;
    size_t keylen;
    char *val;
    size_t vallen;
} Entry;

static HMap g_data;

static bool entry_eq(HNode *lhs, HNode *rhs) {
    Entry *le = (Entry *)lhs;
    Entry *re = (Entry *)rhs;
    return le->keylen == re->keylen && memcmp(le->key, re->key, le->keylen) == 0;
}

static void entry_free(HNode *node) {
    Entry *e = (Entry *)node;
    free(e->key);
    free(e->val);
    free(e);
}

typedef struct Conn {
    int fd;
    bool want_read;
    bool want_write;
    bool want_close;
    Buffer incoming;
    Buffer outgoing;
} Conn;

static Conn **g_fd2conn = NULL;
static size_t g_fd2conn_cap = 0;

static void die(const char *msg) {
    perror(msg);
    exit(1);
}

static void set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) {
        die("fcntl(F_GETFL)");
    }
    if (fcntl(fd, F_SETFL, flags | O_NONBLOCK) == -1) {
        die("fcntl(F_SETFL)");
    }
}

static void fd2conn_put(int fd, Conn *conn) {
    if ((size_t)fd >= g_fd2conn_cap) {
        size_t new_cap = g_fd2conn_cap ? g_fd2conn_cap * 2 : 16;
        while (new_cap <= (size_t)fd) {
            new_cap *= 2;
        }
        g_fd2conn = realloc(g_fd2conn, new_cap * sizeof(Conn *));
        for (size_t i = g_fd2conn_cap; i < new_cap; i++) {
            g_fd2conn[i] = NULL;
        }
        g_fd2conn_cap = new_cap;
    }
    g_fd2conn[fd] = conn;
}

static void do_get(char **args, size_t *arglens, Buffer *out) {
    Entry key = {0};
    key.key = args[1];
    key.keylen = arglens[1];
    key.node.hcode = hash_bytes((const uint8_t *)key.key, key.keylen);

    HNode *node = hm_lookup(&g_data, &key.node, entry_eq);
    if (!node) {
        encode_response(out, RES_NX, NULL, 0);
        return;
    }
    Entry *e = (Entry *)node;
    encode_response(out, RES_OK, (uint8_t *)e->val, e->vallen);
}

static void do_set(char **args, size_t *arglens, Buffer *out) {
    Entry key = {0};
    key.key = args[1];
    key.keylen = arglens[1];
    key.node.hcode = hash_bytes((const uint8_t *)key.key, key.keylen);

    HNode *node = hm_lookup(&g_data, &key.node, entry_eq);
    if (node) {
        Entry *e = (Entry *)node;
        free(e->val);
        e->val = malloc(arglens[2]);
        memcpy(e->val, args[2], arglens[2]);
        e->vallen = arglens[2];
    } else {
        Entry *e = malloc(sizeof(Entry));
        e->key = malloc(arglens[1]);
        memcpy(e->key, args[1], arglens[1]);
        e->keylen = arglens[1];
        e->val = malloc(arglens[2]);
        memcpy(e->val, args[2], arglens[2]);
        e->vallen = arglens[2];
        e->node.next = NULL;
        e->node.hcode = key.node.hcode;
        hm_insert(&g_data, &e->node);
    }
    encode_response(out, RES_OK, NULL, 0);
}

static void do_del(char **args, size_t *arglens, Buffer *out) {
    Entry key = {0};
    key.key = args[1];
    key.keylen = arglens[1];
    key.node.hcode = hash_bytes((const uint8_t *)key.key, key.keylen);

    HNode *node = hm_pop(&g_data, &key.node, entry_eq);
    if (!node) {
        encode_response(out, RES_NX, NULL, 0);
        return;
    }
    entry_free(node);
    encode_response(out, RES_OK, NULL, 0);
}

static void do_request(char **args, size_t *arglens, size_t nargs, Buffer *out) {
    // Responses must be length-prefixed frames on the wire (the client's
    // read_frame() expects a 4-byte length header), so encode the response
    // into a scratch buffer first, then write its length + bytes to `out`.
    Buffer resp;
    buf_init(&resp);
    if (nargs == 2 && strcmp(args[0], "get") == 0) {
        do_get(args, arglens, &resp);
    } else if (nargs == 3 && strcmp(args[0], "set") == 0) {
        do_set(args, arglens, &resp);
    } else if (nargs == 2 && strcmp(args[0], "del") == 0) {
        do_del(args, arglens, &resp);
    } else {
        encode_response(&resp, RES_ERR, NULL, 0);
    }
    uint32_t len = (uint32_t)resp.len;
    buf_append(out, (uint8_t *)&len, 4);
    buf_append(out, resp.data, resp.len);
    buf_free(&resp);
}

static Conn *conn_new(int fd) {
    Conn *conn = malloc(sizeof(Conn));
    conn->fd = fd;
    conn->want_read = true;
    conn->want_write = false;
    conn->want_close = false;
    buf_init(&conn->incoming);
    buf_init(&conn->outgoing);
    return conn;
}

static void conn_destroy(Conn *conn) {
    close(conn->fd);
    buf_free(&conn->incoming);
    buf_free(&conn->outgoing);
    g_fd2conn[conn->fd] = NULL;
    free(conn);
}

static void process_buffered_requests(Conn *conn) {
    while (true) {
        size_t frame_len, payload_len;
        int rv = try_parse_frame(conn->incoming.data, conn->incoming.len, &frame_len, &payload_len);
        if (rv == 0) {
            break;
        }
        if (rv < 0) {
            conn->want_close = true;
            return;
        }
        const uint8_t *payload = conn->incoming.data + 4;
        char **args;
        size_t *arglens;
        size_t nargs;
        if (parse_request(payload, payload_len, &args, &arglens, &nargs) != 0) {
            conn->want_close = true;
            return;
        }
        do_request(args, arglens, nargs, &conn->outgoing);
        free_request_args(args, arglens, nargs);
        buf_consume(&conn->incoming, frame_len);
    }
}

static void handle_read(Conn *conn) {
    uint8_t tmp[64 * 1024];
    ssize_t rv = read(conn->fd, tmp, sizeof(tmp));
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv <= 0) {
        conn->want_close = true;
        return;
    }
    buf_append(&conn->incoming, tmp, (size_t)rv);
    process_buffered_requests(conn);
    conn->want_write = conn->outgoing.len > 0;
}

static void handle_write(Conn *conn) {
    ssize_t rv = write(conn->fd, conn->outgoing.data, conn->outgoing.len);
    if (rv < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        return;
    }
    if (rv < 0) {
        conn->want_close = true;
        return;
    }
    buf_consume(&conn->outgoing, (size_t)rv);
    conn->want_write = conn->outgoing.len > 0;
}

static int make_listener(void) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        die("socket()");
    }

    int val = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &val, sizeof(val));

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        die("bind()");
    }
    if (listen(fd, SOMAXCONN) != 0) {
        die("listen()");
    }
    set_nonblocking(fd);
    return fd;
}

static void accept_new_conn(int listen_fd) {
    struct sockaddr_in client_addr = {0};
    socklen_t addrlen = sizeof(client_addr);
    int connfd = accept(listen_fd, (struct sockaddr *)&client_addr, &addrlen);
    if (connfd < 0) {
        return;
    }
    set_nonblocking(connfd);
    fd2conn_put(connfd, conn_new(connfd));
}

int main(void) {
    signal(SIGPIPE, SIG_IGN);
    hm_init(&g_data);

    int listen_fd = make_listener();
    fprintf(stderr, "listening on 127.0.0.1:%d\n", SERVER_PORT);

    struct pollfd *poll_args = NULL;
    size_t poll_cap = 0;

    while (true) {
        size_t nfds = 1;
        for (size_t i = 0; i < g_fd2conn_cap; i++) {
            if (g_fd2conn[i]) {
                nfds++;
            }
        }
        if (nfds > poll_cap) {
            poll_cap = nfds;
            poll_args = realloc(poll_args, poll_cap * sizeof(struct pollfd));
        }

        poll_args[0] = (struct pollfd){.fd = listen_fd, .events = POLLIN, .revents = 0};

        size_t n = 1;
        for (size_t i = 0; i < g_fd2conn_cap; i++) {
            Conn *conn = g_fd2conn[i];
            if (!conn) {
                continue;
            }
            struct pollfd pfd = {.fd = conn->fd, .events = POLLERR, .revents = 0};
            if (conn->want_read) {
                pfd.events |= POLLIN;
            }
            if (conn->want_write) {
                pfd.events |= POLLOUT;
            }
            poll_args[n++] = pfd;
        }

        int rv = poll(poll_args, (nfds_t)n, -1);
        if (rv < 0 && errno == EINTR) {
            continue;
        }
        if (rv < 0) {
            die("poll()");
        }

        if (poll_args[0].revents & POLLIN) {
            accept_new_conn(listen_fd);
        }

        for (size_t i = 1; i < n; i++) {
            short re = poll_args[i].revents;
            if (!re) {
                continue;
            }
            Conn *conn = g_fd2conn[poll_args[i].fd];
            if (!conn) {
                continue;
            }
            if (re & POLLIN) {
                handle_read(conn);
            }
            if (!conn->want_close && (re & POLLOUT)) {
                handle_write(conn);
            }
            if (conn->want_close || (re & (POLLERR | POLLHUP))) {
                conn_destroy(conn);
            }
        }
    }

    return 0;
}
