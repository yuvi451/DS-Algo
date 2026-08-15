CC := cc
CFLAGS := -std=c11 -Wall -Wextra
RELEASE_FLAGS := -O2
ASAN_FLAGS := -fsanitize=address -g

SRC_DIR := src
TEST_DIR := test
BUILD_DIR := build

.PHONY: all test clean test-hashtable

all: $(BUILD_DIR)/server $(BUILD_DIR)/client

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

test: test-hashtable

test-hashtable: $(BUILD_DIR)/test_hashtable
	$(BUILD_DIR)/test_hashtable

$(BUILD_DIR)/test_hashtable: $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c $(SRC_DIR)/hashtable.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_hashtable.c $(SRC_DIR)/hashtable.c

clean:
	rm -rf $(BUILD_DIR)
