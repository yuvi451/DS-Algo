#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#define K_MAX_MSG 4096
#define SERVER_PORT 1234

typedef enum {
    RES_OK = 0,
    RES_ERR = 1,
    RES_NX = 2,
} ResponseStatus;

typedef struct {
    uint8_t *data;
    size_t len;
    size_t cap;
} Buffer;

void buf_init(Buffer *buf);
void buf_free(Buffer *buf);
void buf_append(Buffer *buf, const uint8_t *data, size_t len);
void buf_consume(Buffer *buf, size_t n);

int encode_request(Buffer *out, char **args, const size_t *arglens, size_t nargs);
int parse_request(const uint8_t *data, size_t len, char ***out_args, size_t **out_arglens, size_t *out_nargs);
void free_request_args(char **args, size_t *arglens, size_t nargs);

/* When datalen == 0, the len/data fields are omitted entirely, so a
 * RES_OK response for an empty-string value is indistinguishable on the
 * wire from a RES_OK/RES_NX response with no value. */
void encode_response(Buffer *out, ResponseStatus status, const uint8_t *data, size_t datalen);
int parse_response(const uint8_t *data, size_t len, ResponseStatus *out_status, const uint8_t **out_data, size_t *out_datalen);

int try_parse_frame(const uint8_t *buf, size_t buf_len, size_t *out_frame_len, size_t *out_payload_len);

int read_full(int fd, uint8_t *buf, size_t n);
int write_all(int fd, const uint8_t *buf, size_t n);
int read_frame(int fd, Buffer *out);
int write_frame(int fd, const uint8_t *payload, size_t len);

#endif
