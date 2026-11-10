---
title: get, set, del — a working key-value server
module: The event-loop server
time: 35 min
---

:::goal
Make it a database! Add a real `runCommand` that stores data in a global
`unordered_map`. Part 6 replaces that map with our own hashtable. Then test
pipelining and many clients at once.
:::

## The data and the real `runCommand`

For now we keep the data in the standard library's hashmap, which you know
from DSA. It's a **global** variable, so every function can reach it (real
Redis also keeps its database as global server state):

```cpp
// For now the data lives in the standard library's hashmap.
// Part 6 swaps in our own HashMap.
unordered_map<string, string> db;

// Runs one command and returns the response payload.
string runCommand(const vector<string> &args) {
    if (args.size() == 2 && args[0] == "get") {
        if (db.count(args[1]) > 0) return encodeResponse(RES_OK, db[args[1]]);
        return encodeResponse(RES_NX);
    }
    if (args.size() == 3 && args[0] == "set") {
        db[args[1]] = args[2];
        return encodeResponse(RES_OK);
    }
    if (args.size() == 2 && args[0] == "del") {
        if (db.erase(args[1]) > 0) return encodeResponse(RES_OK);
        return encodeResponse(RES_NX);
    }
    return encodeResponse(RES_ERR);
}
```

- `db.count(key)` is 1 if the key exists, else 0.
- `db.erase(key)` returns how many keys it removed (0 or 1).
- Each command checks **both** its name **and** the argument count, so `get`
  with no key or `set` with no value become `RES_ERR` instead of reading past
  the end of `args`.

:::task Make it a real key-value server
1. Add `#include <unordered_map>`, the `db` global, and replace the
   placeholder `runCommand` with the real one.
2. Rebuild and run the server, then in terminal 2:

```bash
$ c++ -std=c++17 -Wall src/server.cpp src/protocol.cpp -o build/server
$ build/server
```

```bash
$ build/client get name
$ build/client set name redis
$ build/client get name
$ build/client del name
$ build/client del name
$ build/client get name
$ build/client set onlykey
```
:::

```output
(nil)
OK
redis
OK
(nil)
(nil)
(error) unknown command or wrong number of arguments
```

The second `del` prints `(nil)` because the key was already gone (`RES_NX`).

:::solution
@include code/e-server/s4/src/server.cpp
:::

## Test 1: pipelining

Let's prove `handleRequests` handles several requests arriving in **one**
read. This program frames three requests back to back and sends them with a
**single** `write()`, then reads three replies:

@include code/e-server/pipeline.cpp title=scratch/pipeline.cpp

:::task Pipeline test
With the server running:

```bash
$ c++ -std=c++17 -Wall scratch/pipeline.cpp src/protocol.cpp -o build/pipeline
$ build/pipeline
```
:::

```output
sending 76 bytes in one write()
reply 1: status=0 data=""
reply 2: status=0 data="c++"
reply 3: status=0 data=""
```

(Status 0 = `RES_OK`.) Try changing `while (true)` in `handleRequests` to run
only once, rebuild the server, and run the pipeline test again: it hangs
after reply 1. That's the classic pipelining bug. Put the loop back!

## Test 2: the frozen-client experiment, again

:::task Concurrency test
1. Server running in terminal 1.
2. Terminal 2: `nc 127.0.0.1 1234`, and **type nothing**.
3. Terminal 3:

```bash
$ build/client set a 1
$ build/client get a
```
:::

```output
OK
1
```

The idle `nc` connection no longer blocks anyone. Remember Lesson 5.1, where
the same experiment froze the hello server? **That's the event loop working.**

(If you now type `hello` + Enter into the `nc` window, the server closes that
connection. Typed text isn't a valid frame: the first 4 characters `hell` are
read as a length of about 1.8 billion, which is far over `MAX_MSG`, so the
server refuses to trust it.)

:::recap
- `runCommand` checks the command name **and** argument count and replies `RES_OK`/`RES_NX`/`RES_ERR`.
- The data lives in a global `db`. For now it's an `unordered_map`.
- Pipelined requests and idle clients both work. 🎉 **You have a working Redis-like server.**
:::
