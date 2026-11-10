---
title: Plug the hashtable into the server
module: Our own hashtable
time: 20 min
---

:::goal
Replace the `unordered_map` in the server with our `HashMap`. Only the `db`
line and `runCommand` change. The networking code stays exactly the same.
After this lesson, `server.cpp` is **final**.
:::

## The swap

Before (Part 5):

```cpp
unordered_map<string, string> db;
```

After:

```cpp
HashMap db;
```

`runCommand` now calls our methods instead of the map's:

```cpp
// Runs one command and returns the response payload.
string runCommand(const vector<string> &args) {
    if (args.size() == 2 && args[0] == "get") {
        string val;
        if (db.get(args[1], val)) return encodeResponse(RES_OK, val);
        return encodeResponse(RES_NX);
    }
    if (args.size() == 3 && args[0] == "set") {
        db.set(args[1], args[2]);
        return encodeResponse(RES_OK);
    }
    if (args.size() == 2 && args[0] == "del") {
        if (db.del(args[1])) return encodeResponse(RES_OK);
        return encodeResponse(RES_NX);
    }
    return encodeResponse(RES_ERR);
}
```

| Old (`unordered_map`) | New (`HashMap`) |
|---|---|
| `db.count(k) > 0` then `db[k]` | `db.get(k, val)` fills `val`, returns `false` if missing |
| `db[k] = v` | `db.set(k, v)` |
| `db.erase(k) > 0` | `db.del(k)` |

:::task Swap the storage engine
1. In `server.cpp`: remove `#include <unordered_map>`, add
   `#include "hashtable.h"` (next to `"protocol.h"`).
2. Change `db` to a `HashMap` and update `runCommand` as above. **Don't touch
   anything else.**
3. The server is now three `.cpp` files:

```bash
$ c++ -std=c++17 -Wall -O2 src/server.cpp src/hashtable.cpp src/protocol.cpp -o build/server
$ build/server
```

4. Terminal 2: run the same commands as before, then add 2,000 keys with a
   shell loop (making the table grow several times) and read some back:

```bash
$ build/client set name redis
$ build/client get name
$ build/client del name
$ build/client get name
$ for i in $(seq 1 2000); do build/client set key$i val$i > /dev/null; done
$ build/client get key1
$ build/client get key1999
```
:::

```output
OK
redis
OK
(nil)
val1
val1999
```

:::hint Hint: "Undefined symbols … HashMap::get"
You forgot `src/hashtable.cpp` in the compile command. The linker needs its
definitions.
:::

:::cpp Bash: `for i in $(seq 1 2000); do …; done`
`seq 1 2000` prints the numbers 1 to 2000. The loop runs the command once for
each, with `$i` replaced by the number. `> /dev/null` throws the `OK` output
away.
:::

:::solution This is the final src/server.cpp
@include ../src/server.cpp
:::

:::recap
- `HashMap db;` replaces the `unordered_map`. `runCommand` calls `get`/`set`/`del`.
- The network code didn't change at all.
- 🎉 **Every source file in `src/` is now final.**
:::
