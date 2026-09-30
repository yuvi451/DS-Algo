CXX := c++
CXXFLAGS := -std=c++17 -Wall -Wextra
RELEASE := $(CXXFLAGS) -O2
ASAN := $(CXXFLAGS) -fsanitize=address -g

HEADERS := src/hashtable.h src/protocol.h
SERVER_SRC := src/server.cpp src/hashtable.cpp src/protocol.cpp
CLIENT_SRC := src/client.cpp src/protocol.cpp

.PHONY: all bench test test-hashtable test-protocol test-integration clean

all: build/server build/client
bench: build/loadtest
test: test-hashtable test-protocol test-integration

build:
	mkdir -p build

# Release binaries
build/server: $(SERVER_SRC) $(HEADERS) | build
	$(CXX) $(RELEASE) -o $@ $(SERVER_SRC)

build/client: $(CLIENT_SRC) $(HEADERS) | build
	$(CXX) $(RELEASE) -o $@ $(CLIENT_SRC)

build/loadtest: bench/loadtest.cpp src/protocol.cpp $(HEADERS) | build
	$(CXX) $(RELEASE) -pthread -o $@ bench/loadtest.cpp src/protocol.cpp

# ASan binaries for tests
build/server_asan: $(SERVER_SRC) $(HEADERS) | build
	$(CXX) $(ASAN) -o $@ $(SERVER_SRC)

build/client_asan: $(CLIENT_SRC) $(HEADERS) | build
	$(CXX) $(ASAN) -o $@ $(CLIENT_SRC)

build/test_hashtable: test/test_hashtable.cpp src/hashtable.cpp $(HEADERS) | build
	$(CXX) $(ASAN) -o $@ test/test_hashtable.cpp src/hashtable.cpp

build/test_protocol: test/test_protocol.cpp src/protocol.cpp $(HEADERS) | build
	$(CXX) $(ASAN) -o $@ test/test_protocol.cpp src/protocol.cpp

test-hashtable: build/test_hashtable
	build/test_hashtable

test-protocol: build/test_protocol
	build/test_protocol

test-integration: build/server_asan build/client_asan
	test/test_integration.sh

clean:
	rm -rf build
