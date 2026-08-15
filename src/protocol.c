#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>
#include "protocol.h"

void buf_init(Buffer *buf) {
    buf->data = NULL;
    buf->len = 0;
    buf->cap = 0;
}

void buf_free(Buffer *buf) {
    free(buf->data);
    buf_init(buf);
}

void buf_append(Buffer *buf, const uint8_t *data, size_t len) {
    if (buf->len + len > buf->cap) {
        size_t new_cap = buf->cap ? buf->cap * 2 : 64;
        while (new_cap < buf->len + len) {
            new_cap *= 2;
        }
        buf->data = realloc(buf->data, new_cap);
        buf->cap = new_cap;
    }
    memcpy(buf->data + buf->len, data, len);
    buf->len += len;
}

void buf_consume(Buffer *buf, size_t n) {
    assert(n <= buf->len);
    memmove(buf->data, buf->data + n, buf->len - n);
    buf->len -= n;
}

int encode_request(Buffer *out, char **args, const size_t *arglens, size_t nargs) {
    uint32_t n = (uint32_t)nargs;
    buf_append(out, (uint8_t *)&n, 4);
    for (size_t i = 0; i < nargs; i++) {
        uint32_t l = (uint32_t)arglens[i];
        buf_append(out, (uint8_t *)&l, 4);
        buf_append(out, (uint8_t *)args[i], arglens[i]);
    }
    if (out->len > K_MAX_MSG) {
        return -1;
    }
    return 0;
}

int parse_request(const uint8_t *data, size_t len, char ***out_args, size_t **out_arglens, size_t *out_nargs) {
    if (len < 4) {
        return -1;
    }
    uint32_t nargs;
    memcpy(&nargs, data, 4);
    if (nargs > 1024) {
        return -1;
    }
    size_t pos = 4;

    char **args = malloc(sizeof(char *) * (nargs ? nargs : 1));
    size_t *arglens = malloc(sizeof(size_t) * (nargs ? nargs : 1));

    for (uint32_t i = 0; i < nargs; i++) {
        if (pos + 4 > len) {
            for (uint32_t j = 0; j < i; j++) {
                free(args[j]);
            }
            free(args);
            free(arglens);
            return -1;
        }
        uint32_t l;
        memcpy(&l, data + pos, 4);
        pos += 4;
        if (pos + l > len) {
            for (uint32_t j = 0; j < i; j++) {
                free(args[j]);
            }
            free(args);
            free(arglens);
            return -1;
        }
        char *s = malloc(l + 1);
        memcpy(s, data + pos, l);
        s[l] = '\0';
        args[i] = s;
        arglens[i] = l;
        pos += l;
    }
    if (pos != len) {
        for (uint32_t j = 0; j < nargs; j++) {
            free(args[j]);
        }
        free(args);
        free(arglens);
        return -1;
    }

    *out_args = args;
    *out_arglens = arglens;
    *out_nargs = nargs;
    return 0;
}

void free_request_args(char **args, size_t *arglens, size_t nargs) {
    for (size_t i = 0; i < nargs; i++) {
        free(args[i]);
    }
    free(args);
    free(arglens);
}

void encode_response(Buffer *out, ResponseStatus status, const uint8_t *data, size_t datalen) {
    uint8_t s = (uint8_t)status;
    buf_append(out, &s, 1);
    if (data && datalen > 0) {
        uint32_t l = (uint32_t)datalen;
        buf_append(out, (uint8_t *)&l, 4);
        buf_append(out, data, datalen);
    }
}

int parse_response(const uint8_t *data, size_t len, ResponseStatus *out_status, const uint8_t **out_data, size_t *out_datalen) {
    if (len < 1) {
        return -1;
    }
    *out_status = (ResponseStatus)data[0];
    if (len == 1) {
        *out_data = NULL;
        *out_datalen = 0;
        return 0;
    }
    if (len < 5) {
        return -1;
    }
    uint32_t l;
    memcpy(&l, data + 1, 4);
    if (5 + (size_t)l != len) {
        return -1;
    }
    *out_data = data + 5;
    *out_datalen = l;
    return 0;
}

int try_parse_frame(const uint8_t *buf, size_t buf_len, size_t *out_frame_len, size_t *out_payload_len) {
    if (buf_len < 4) {
        return 0;
    }
    uint32_t len;
    memcpy(&len, buf, 4);
    if (len > K_MAX_MSG) {
        return -1;
    }
    if (buf_len < 4 + (size_t)len) {
        return 0;
    }
    *out_frame_len = 4 + len;
    *out_payload_len = len;
    return 1;
}

int read_full(int fd, uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = read(fd, buf, n);
        if (rv <= 0) {
            return -1;
        }
        n -= (size_t)rv;
        buf += rv;
    }
    return 0;
}

int write_all(int fd, const uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t rv = write(fd, buf, n);
        if (rv <= 0) {
            return -1;
        }
        n -= (size_t)rv;
        buf += rv;
    }
    return 0;
}

int read_frame(int fd, Buffer *out) {
    uint8_t head[4];
    if (read_full(fd, head, 4) != 0) {
        return -1;
    }
    uint32_t len;
    memcpy(&len, head, 4);
    if (len > K_MAX_MSG) {
        return -1;
    }
    buf_append(out, head, 4);
    if (len > 0) {
        uint8_t tmp[K_MAX_MSG];
        if (read_full(fd, tmp, len) != 0) {
            return -1;
        }
        buf_append(out, tmp, len);
    }
    return 0;
}

int write_frame(int fd, const uint8_t *payload, size_t len) {
    if (len > K_MAX_MSG) {
        return -1;
    }
    uint8_t head[4];
    uint32_t l = (uint32_t)len;
    memcpy(head, &l, 4);
    if (write_all(fd, head, 4) != 0) {
        return -1;
    }
    if (len > 0 && write_all(fd, payload, len) != 0) {
        return -1;
    }
    return 0;
}
