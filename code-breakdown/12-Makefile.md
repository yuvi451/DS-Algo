# 12 — `Makefile`

**What it is:** the build script. `make` reads it and runs the compiler
commands needed to produce each program, and only rebuilds what changed.

```sh
make                    # build/server and build/client
make test               # all tests
make bench              # build/loadtest
make clean              # delete build/
```

---

## How a Makefile rule works

```make
target: prerequisites
	recipe (the command; MUST start with a TAB, not spaces)
```

"To make `target`, first make sure every prerequisite exists and is up to
date. If any prerequisite is **newer** than the target (by file
modification time), run the recipe." That's how `make` avoids recompiling
everything after a one-line change.

---

## Lines 1–4: compiler settings

```make
CXX := c++
CXXFLAGS := -std=c++17 -Wall -Wextra
RELEASE := $(CXXFLAGS) -O2
ASAN := $(CXXFLAGS) -fsanitize=address -g
```

Variables. `:=` assigns once; `$(NAME)` uses a variable.

| Flag | Meaning |
|---|---|
| `c++` | The system C++ compiler (Apple Clang on macOS, usually g++ on Linux) |
| `-std=c++17` | Use the C++17 language standard (needed for `std::optional`, `std::string_view`) |
| `-Wall -Wextra` | Turn on most warnings. The project builds with zero warnings. |
| `-O2` | Optimise for speed. Used for the real binaries and the benchmark. |
| `-fsanitize=address` | **AddressSanitizer (ASan)**: adds runtime checks that crash the program with a detailed report on use-after-free, buffer overflow, double free, and memory leaks. Makes the program ~2× slower. Used for tests. |
| `-g` | Include debug info, so ASan reports and debuggers show file names and line numbers |

Why ASan matters here: the hashtable manages memory by hand (`new`,
`delete`, raw pointers). Those bugs often don't crash immediately; they
corrupt memory silently. ASan catches them the moment they happen.

---

## Lines 6–8: file lists

```make
HEADERS := src/hashtable.h src/protocol.h
SERVER_SRC := src/server.cpp src/hashtable.cpp src/protocol.cpp
CLIENT_SRC := src/client.cpp src/protocol.cpp
```

Which `.cpp` files make up each program. The client doesn't need the
hashtable. `protocol.cpp` is shared by everything.

---

## Line 10: `.PHONY`

```make
.PHONY: all bench test test-hashtable test-protocol test-integration clean
```

These targets are *actions*, not files. Without `.PHONY`, if a file named
`test` or `clean` ever existed in the folder, `make` would think the target
was already "built" and do nothing.

---

## Lines 12–17: top-level targets

```make
all: build/server build/client
bench: build/loadtest
test: test-hashtable test-protocol test-integration

build:
	mkdir -p build
```

- `all` is the first target in the file, so plain `make` runs it.
- `test` runs the three test targets in order.
- `build` creates the output folder. `mkdir -p` doesn't complain if it
  already exists.

---

## Lines 19–27: release binaries

```make
build/server: $(SERVER_SRC) $(HEADERS) | build
	$(CXX) $(RELEASE) -o $@ $(SERVER_SRC)
```

- Rebuild `build/server` if any of its `.cpp` files **or any header**
  changed. (Headers are listed because a change to a `.h` changes how every
  file including it compiles.)
- **`| build`** is an *order-only* prerequisite: "the `build/` folder must
  exist first, but don't rebuild just because its timestamp changed". A
  folder's timestamp changes every time a file inside it is written, which
  would otherwise cause endless rebuilds.
- **`$@`** means "this rule's target", here `build/server`. `-o $@` names
  the output file.

**One command compiles everything:** all `.cpp` files for a program are
passed to the compiler at once, which compiles and links them in one step.
Larger projects compile each `.cpp` to a `.o` object file separately, so a
change only recompiles one file. For ~1,000 lines, a full rebuild takes a
couple of seconds, so the simpler form wins.

```make
build/loadtest: bench/loadtest.cpp src/protocol.cpp $(HEADERS) | build
	$(CXX) $(RELEASE) -pthread -o $@ bench/loadtest.cpp src/protocol.cpp
```

`-pthread` enables thread support, needed for `std::thread`.

---

## Lines 29–40: ASan binaries

```make
build/server_asan: $(SERVER_SRC) $(HEADERS) | build
	$(CXX) $(ASAN) -o $@ $(SERVER_SRC)
...
build/test_hashtable: test/test_hashtable.cpp src/hashtable.cpp $(HEADERS) | build
	$(CXX) $(ASAN) -o $@ test/test_hashtable.cpp src/hashtable.cpp
```

The same programs built with AddressSanitizer, plus the two unit-test
programs. The `_asan` suffix keeps them separate from the fast release
builds.

---

## Lines 42–49: test targets

```make
test-hashtable: build/test_hashtable
	build/test_hashtable

test-protocol: build/test_protocol
	build/test_protocol

test-integration: build/server_asan build/client_asan
	test/test_integration.sh
```

Build the test binaries if needed, then run them. If a test program exits
with a non-zero status (a failed `assert`), `make` stops and reports the
failure.

---

## Lines 51–52: clean

```make
clean:
	rm -rf build
```

Delete every build output. The next `make` rebuilds from scratch.
