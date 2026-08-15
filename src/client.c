#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include "protocol.h"

static int connect_to_server(void) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket()");
        exit(1);
    }

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        perror("connect()");
        exit(1);
    }
    return fd;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s <cmd> [args...]\n", argv[0]);
        return 1;
    }

    size_t nargs = (size_t)(argc - 1);
    char **args = &argv[1];
    size_t *arglens = malloc(nargs * sizeof(size_t));
    for (size_t i = 0; i < nargs; i++) {
        arglens[i] = strlen(args[i]);
    }

    Buffer req;
    buf_init(&req);
    if (encode_request(&req, args, arglens, nargs) != 0) {
        fprintf(stderr, "request too large\n");
        return 1;
    }

    int fd = connect_to_server();
    if (write_frame(fd, req.data, req.len) != 0) {
        fprintf(stderr, "write_frame failed\n");
        return 1;
    }

    Buffer resp;
    buf_init(&resp);
    if (read_frame(fd, &resp) != 0) {
        fprintf(stderr, "read_frame failed\n");
        return 1;
    }

    ResponseStatus status;
    const uint8_t *data;
    size_t datalen;
    if (parse_response(resp.data + 4, resp.len - 4, &status, &data, &datalen) != 0) {
        fprintf(stderr, "bad response\n");
        return 1;
    }

    switch (status) {
    case RES_OK:
        if (datalen > 0) {
            fwrite(data, 1, datalen, stdout);
            fputc('\n', stdout);
        } else {
            printf("OK\n");
        }
        break;
    case RES_NX:
        printf("(nil)\n");
        break;
    case RES_ERR:
        printf("(error) unknown command or wrong number of arguments\n");
        break;
    }

    close(fd);
    buf_free(&req);
    buf_free(&resp);
    free(arglens);
    return 0;
}
