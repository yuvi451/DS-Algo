---
title: Set up your workspace
module: Start here
time: 20 min
---

:::goal
Install a C++ compiler, learn the handful of terminal commands this course
uses, create the project folder, and compile your first program with the
exact compiler flags we'll use for the whole project.
:::

## Why the terminal?

In DSA practice you probably pressed a "Run" button in an online judge or an
IDE. A server is different: it's a program that **keeps running** and waits
for other programs to talk to it. To see that happen, you'll often run **two
programs at the same time**: the server in one terminal window and the client
in another. The terminal makes this easy and shows you exactly what happens.

:::warn Use macOS or Linux
Everything in this course uses the **POSIX socket API**, which macOS and
Linux share. On Windows, install **WSL** (Windows Subsystem for Linux) and
follow the Linux instructions inside it. The code was written and tested on
macOS. The few places where Linux behaves differently are pointed out.
:::

## Step 1: Install a compiler

**macOS:** open the *Terminal* app and run:

```bash
$ xcode-select --install
```

**Linux (Ubuntu/Debian/WSL):**

```bash
$ sudo apt update && sudo apt install build-essential netcat-openbsd
```

Check it worked:

```bash
$ c++ --version
```

You should see something like `Apple clang version ...` or `g++ (Ubuntu ...)`.
The exact version doesn't matter as long as it supports C++17, and anything
from the last 7 years does.

:::why Why `c++` and not `g++`?
`c++` is a generic name that points to whatever C++ compiler your system has:
`clang++` on macOS, usually `g++` on Linux. Using `c++` means the same
commands work on both.
:::

## Step 2: The only terminal commands you need

| Command | What it does | Example |
|---|---|---|
| `pwd` | Print the folder you're in | `pwd` |
| `ls` | List files in this folder | `ls src` |
| `cd` | Change folder | `cd ~/microredis` |
| `mkdir -p` | Make folders (`-p`: also make parents, no error if it exists) | `mkdir -p src test` |
| `cat` | Print a file's contents | `cat src/server.cpp` |
| **Ctrl + C** | **Stop** the program running in this terminal | (stops a server) |
| `↑` arrow | Bring back the previous command | |

You also need **two terminal windows** side by side. On macOS press
**Cmd + T** for a new tab or **Cmd + N** for a new window. Most Linux
terminals use **Ctrl + Shift + T**.

You'll need a code editor too. VS Code is a good free choice, but any editor
works.

## Step 3: Create the project folder

We'll keep everything in one folder called `microredis` in your home
directory (`~` is shorthand for your home folder):

```bash
$ mkdir -p ~/microredis/src ~/microredis/test ~/microredis/scratch ~/microredis/build ~/microredis/bench
$ cd ~/microredis
$ ls
bench   build   scratch src     test
```

Here's what each folder is for:

```text
microredis/
├── src/       the real project: server, client, protocol, hashtable
├── test/      automated tests for src/
├── bench/     a load-testing tool (last part of the course)
├── scratch/   practice programs and experiments, thrown away later
└── build/     compiled programs go here (never edit anything in it)
```

:::why Why keep compiled programs in `build/`?
Compiling turns your `.cpp` text files into an executable file of machine
code. Keeping those files in their own folder means your source folders stay
clean, and you can wipe all compiled output with one `rm -rf build`.
:::

## Step 4: Your first compile

Every C++ program goes through this pipeline:

```text
 hello.cpp  ──►  compiler (c++)  ──►  build/hello  ──►  run it: build/hello
 (text you write)                   (machine code)
```

Here is the compile command you'll use all the time. Learn it once:

```bash
$ c++ -std=c++17 -Wall scratch/hello.cpp -o build/hello
```

| Piece | Meaning | Why we want it |
|---|---|---|
| `c++` | Run the C++ compiler | |
| `-std=c++17` | Use the C++17 language standard | A modern version of C++, so everything in this course works |
| `-Wall` | Turn on the useful warnings | The compiler catches many bugs for free, like unused variables or comparing signed with unsigned numbers. **Treat every warning as a bug.** |
| `scratch/hello.cpp` | The input source file(s) | You can list several `.cpp` files and they're combined into one program |
| `-o build/hello` | Name of the output program | Without `-o` you'd get a file called `a.out` |

To **run** the program, type its path: `build/hello`. (On some systems you
must write `./build/hello`. Both mean "the program in the build folder
here".)

:::task Compile and run hello world
1. Create the file `scratch/hello.cpp` in your editor.
2. Write a `main` function that prints `Hello from MicroRedis!` followed by a
   newline, using `cout`.
3. Compile it with the command above, then run it.

```bash
$ c++ -std=c++17 -Wall scratch/hello.cpp -o build/hello
$ build/hello
```
:::

```output
Hello from MicroRedis!
```

:::hint Hint: cout
`cout << "text" << endl;` prints text and a newline. You need
`#include <iostream>` and `using namespace std;` at the top.
:::

:::solution
@include code/a-basics/hello.cpp title=scratch/hello.cpp
:::

## When the compiler complains

You will see errors. Everyone does, all the time. Here's how to read one:

```text
scratch/hello.cpp:4:5: error: use of undeclared identifier 'cout'
    cout << "Hello from MicroRedis!" << endl;
    ^
```

- `scratch/hello.cpp:4:5`: **file : line : column**. Go there first.
- `error:` means the program did not compile. `warning:` means it compiled,
  but something looks wrong.
- Read the **first** error first. Later errors are often caused by the first
  one.
- Here the fix is the missing `#include <iostream>` (or `using namespace std;`).

:::recap
- You have a compiler, a project folder, and two terminal windows.
- You compile with `c++ -std=c++17 -Wall <files> -o build/<name>`
  and run with `build/<name>`.
- **Ctrl + C** stops a running program. You'll use it a lot on servers.
:::
