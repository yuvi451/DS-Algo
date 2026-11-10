---
title: A Makefile so you never type compile commands again
module: Ship it
time: 25 min
---

:::goal
You now have several programs (server, client, two test suites), each with a
long compile command. Write the project's **Makefile** so `make` builds
everything, `make test` runs every test, and only programs whose files
changed get rebuilt.
:::

## What `make` does

`make` reads a file named `Makefile` that lists **rules**:

```make
target: files it depends on
	command to build the target
```

> "To build *target*, look at the files it depends on. If any of them is
> **newer** than the target (or the target doesn't exist yet), run the
> command."

That "newer than" check is the magic: after you edit `client.cpp`, `make`
rebuilds the client but not the server.

:::warn The command line must start with a TAB
Not spaces, a real **Tab** character. This is the most famous gotcha in
computing. Spaces give the error `missing separator`. Configure your editor
to keep tabs in Makefiles.
:::

## Variables

```make
CXX = c++
FLAGS = -std=c++17 -Wall -O2
```

`NAME = value` defines a variable and `$(NAME)` uses it. `-O2` tells the
compiler to **optimize** for speed, which matters for the benchmark.

## The whole Makefile

@include ../Makefile

How to read it:

- Each `build/...` rule lists the `.cpp` **and** `.h` files the program is made
  from. Headers never appear in the compile command, but listing them means
  editing `protocol.h` rebuilds everything that uses it.
- `mkdir -p build` makes sure the folder exists before compiling into it.
- `all` is the **first** rule, so plain `make` = `make all`.
- `test` first builds what it needs, then runs both unit tests and the
  integration test (next lesson). `make` stops at the first failure.
- `.PHONY` lists rules that are **names for actions**, not files. Without it,
  a stray file called `test` would make `make test` think it's "already up to
  date".

| Command | Does |
|---|---|
| `make` | Builds `build/server` and `build/client` |
| `make test` | Unit tests + integration test |
| `make bench` | Builds `build/loadtest` |
| `make clean` | Removes `build/` |

:::task Write the Makefile
1. Create `Makefile` (capital M, no extension) in the project root with the
   content above. **Use real tabs** before the commands.
2. Try it:

```bash
$ make clean
$ make
$ make
$ touch src/client.cpp
$ make
$ make build/test_hashtable && build/test_hashtable
```
:::

```output
rm -rf build
mkdir -p build
c++ -std=c++17 -Wall -O2 -o build/server src/server.cpp src/hashtable.cpp src/protocol.cpp
mkdir -p build
c++ -std=c++17 -Wall -O2 -o build/client src/client.cpp src/protocol.cpp
make: Nothing to be done for `all'.
mkdir -p build
c++ -std=c++17 -Wall -O2 -o build/client src/client.cpp src/protocol.cpp
mkdir -p build
c++ -std=c++17 -Wall -O2 -o build/test_hashtable test/test_hashtable.cpp src/hashtable.cpp
testSetAndGet: OK
testDel: OK
testGrowing: OK
All hashtable tests passed.
```

- The second `make` does nothing, since nothing changed.
- After `touch src/client.cpp` (which updates its timestamp), only the client
  is rebuilt.

(Linux prints `make: Nothing to be done for 'all'.` with straight quotes.)
`make test` needs the script from the next lesson.

:::hint Hint: `Makefile:7: *** missing separator. Stop.`
Line 7 starts with spaces instead of a Tab. In VS Code, click "Spaces: 4"
in the status bar and choose "Indent Using Tabs", then retype the indent.
:::

:::recap
- Rule = `target: files` + Tab-indented command. Rebuilt only if a file is newer than the target.
- `$(NAME)` uses a variable. `.PHONY` marks action names, not files.
- `make`, `make test`, `make bench`, `make clean`.
:::
