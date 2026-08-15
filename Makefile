CXX := c++
CXXFLAGS := -std=c++17 -Wall -Wextra
RELEASE_FLAGS := -O2
ASAN_FLAGS := -fsanitize=address -g

SRC_DIR := src
TEST_DIR := test
BUILD_DIR := build
BENCH_DIR := bench

.PHONY: all test clean test-hashtable test-protocol test-integration bench

all: $(BUILD_DIR)/server $(BUILD_DIR)/client

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/server: $(SRC_DIR)/server.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/hashtable.h $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/server.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/protocol.cpp

$(BUILD_DIR)/client: $(SRC_DIR)/client.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -o $@ $(SRC_DIR)/client.cpp $(SRC_DIR)/protocol.cpp

$(BUILD_DIR)/server_asan: $(SRC_DIR)/server.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/hashtable.h $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(SRC_DIR)/server.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/protocol.cpp

$(BUILD_DIR)/client_asan: $(SRC_DIR)/client.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(SRC_DIR)/client.cpp $(SRC_DIR)/protocol.cpp

bench: $(BUILD_DIR)/loadtest

$(BUILD_DIR)/loadtest: $(BENCH_DIR)/loadtest.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -pthread -o $@ $(BENCH_DIR)/loadtest.cpp $(SRC_DIR)/protocol.cpp

test: test-hashtable test-protocol test-integration

test-hashtable: $(BUILD_DIR)/test_hashtable
	$(BUILD_DIR)/test_hashtable

test-protocol: $(BUILD_DIR)/test_protocol
	$(BUILD_DIR)/test_protocol

test-integration: $(BUILD_DIR)/server_asan $(BUILD_DIR)/client_asan
	$(TEST_DIR)/test_integration.sh

$(BUILD_DIR)/test_hashtable: $(TEST_DIR)/test_hashtable.cpp $(SRC_DIR)/hashtable.cpp $(SRC_DIR)/hashtable.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_hashtable.cpp $(SRC_DIR)/hashtable.cpp

$(BUILD_DIR)/test_protocol: $(TEST_DIR)/test_protocol.cpp $(SRC_DIR)/protocol.cpp $(SRC_DIR)/protocol.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(ASAN_FLAGS) -o $@ $(TEST_DIR)/test_protocol.cpp $(SRC_DIR)/protocol.cpp

clean:
	rm -rf $(BUILD_DIR)
