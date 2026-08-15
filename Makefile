CC := cc
CFLAGS := -std=c11 -Wall -Wextra
RELEASE_FLAGS := -O2
ASAN_FLAGS := -fsanitize=address -g

SRC_DIR := src
TEST_DIR := test
BUILD_DIR := build

.PHONY: all test clean test-hashtable test-protocol test-integration

all: $(BUILD_DIR)/server $(BUILD_DIR)/client

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/server: $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c $(SRC_DIR)/hashtable.h $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c

$(BUILD_DIR)/client: $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c

$(BUILD_DIR)/server_asan: $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c $(SRC_DIR)/hashtable.h $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(SRC_DIR)/server.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/protocol.c

$(BUILD_DIR)/client_asan: $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(SRC_DIR)/client.c $(SRC_DIR)/protocol.c

test: test-hashtable test-protocol test-integration

test-hashtable: $(BUILD_DIR)/test_hashtable
	$(BUILD_DIR)/test_hashtable

test-protocol: $(BUILD_DIR)/test_protocol
	$(BUILD_DIR)/test_protocol

test-integration: $(BUILD_DIR)/server_asan $(BUILD_DIR)/client_asan
	$(TEST_DIR)/test_integration.sh

$(BUILD_DIR)/test_hashtable: $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/hashtable.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c

$(BUILD_DIR)/test_protocol: $(TEST_DIR)/test_protocol.c $(SRC_DIR)/protocol.c $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_protocol.c $(SRC_DIR)/protocol.c

clean:
	rm -rf $(BUILD_DIR)
