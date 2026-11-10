CXX = c++
FLAGS = -std=c++17 -Wall -O2

all: build/server build/client

build/server: src/server.cpp src/hashtable.cpp src/protocol.cpp src/hashtable.h src/protocol.h
	mkdir -p build
	$(CXX) $(FLAGS) -o build/server src/server.cpp src/hashtable.cpp src/protocol.cpp

build/client: src/client.cpp src/protocol.cpp src/protocol.h
	mkdir -p build
	$(CXX) $(FLAGS) -o build/client src/client.cpp src/protocol.cpp

build/loadtest: bench/loadtest.cpp src/protocol.cpp src/protocol.h
	mkdir -p build
	$(CXX) $(FLAGS) -pthread -o build/loadtest bench/loadtest.cpp src/protocol.cpp

build/test_hashtable: test/test_hashtable.cpp src/hashtable.cpp src/hashtable.h
	mkdir -p build
	$(CXX) $(FLAGS) -o build/test_hashtable test/test_hashtable.cpp src/hashtable.cpp

build/test_protocol: test/test_protocol.cpp src/protocol.cpp src/protocol.h
	mkdir -p build
	$(CXX) $(FLAGS) -o build/test_protocol test/test_protocol.cpp src/protocol.cpp

bench: build/loadtest

test: build/test_hashtable build/test_protocol build/server build/client
	build/test_hashtable
	build/test_protocol
	test/test_integration.sh

clean:
	rm -rf build

.PHONY: all bench test clean
