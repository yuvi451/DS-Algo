# 08 — `bench/loadtest.cpp`

**What it is:** the benchmark that produced the resume numbers. It starts N
threads (default 200); each opens one connection to the server and sends
requests as fast as it can for a fixed time (default 10 s), timing every
request. At the end it prints throughput and latency percentiles.

```sh
build/server &
build/loadtest 200 10
# clients=200 duration_target=10.0s actual_wall=10.001s failed_connects=0
# total_ops=1842804 throughput=184252.9 ops/sec
# latency_us: min=182.1 p50=1017.6 p90=1235.2 p99=1948.8 max=21110.4 mean=1084.0
```

Only the benchmark uses threads. The server itself stays single-threaded.

---

## Lines 1–4: header comment

```cpp
// Closed-loop load test: N threads, one connection each, alternating set/get
// and timing every round trip.
//
// usage: loadtest [n_clients=200] [duration_sec=10]
```

**Closed loop** means each client waits for its reply before sending the
next request, so there are never more than N requests in flight. (An **open
loop** test sends at a fixed rate regardless of replies, which better shows
how latency explodes under overload.)

---

## Lines 6–17: includes

```cpp
#include <algorithm>  // std::sort
#include <chrono>     // clocks and durations
#include <cstdio>     // printf
#include <cstdlib>    // std::atoi, std::atof
#include <numeric>    // std::accumulate
#include <string>
#include <thread>     // std::thread
#include <vector>

#include <unistd.h>   // close

#include "../src/protocol.h"
```

`"../src/protocol.h"` is a relative path: go up from `bench/` and into `src/`.

---

## Lines 19–24: types

```cpp
using Clock = std::chrono::steady_clock;

struct ThreadResult {
    std::vector<double> latenciesUs;
    bool connectFailed = false;
};
```

- **`steady_clock`**: a clock that only moves forward at a constant rate.
  Use it to measure durations. (`system_clock` is the wall-clock time, which
  can jump if the computer's time is adjusted, making durations wrong.)
- **`ThreadResult`**: each thread records its own latencies (in
  microseconds) here. Each thread gets its **own** `ThreadResult`, so threads
  never write to shared data and no locks are needed.

---

## Lines 26–52: `worker`, what each thread does

```cpp
static void worker(int threadId, Clock::time_point deadline, ThreadResult &result) {
    int fd = connectToServer();
    if (fd < 0) {
        result.connectFailed = true;
        return;
    }
```

Open one connection and keep it for the whole test (a **persistent
connection**). Opening a new TCP connection per request would measure
handshake cost, not the server.

> **CN refresher — persistent connections:** each new TCP connection costs a
> 3-way handshake (one round trip) before any data flows, plus a teardown
> afterwards. Reusing one connection avoids that, which is why databases use
> connection pools and HTTP/1.1 added "keep-alive".

```cpp
    for (long i = 0; Clock::now() < deadline; i++) {
        std::string key = "lt:" + std::to_string(threadId) + ":" + std::to_string(i / 2);
        std::vector<std::string> args;
        if (i % 2 == 0) {
            args = {"set", key, "v" + std::to_string(i)};
        } else {
            args = {"get", key};
        }
        Buffer request;
        encodeRequest(request, args);
```

Keep going until the deadline. Requests alternate:

```
i=0: set lt:7:0 v0
i=1: get lt:7:0
i=2: set lt:7:1 v2
i=3: get lt:7:1
...
```

So every thread writes new keys (the hashtable keeps growing and resizing
during the test) and reads back what it just wrote. The thread id in the key
keeps threads from touching each other's keys.

```cpp
        auto t0 = Clock::now();
        if (!writeFrame(fd, request) || !readFrame(fd)) {
            break;
        }
        auto t1 = Clock::now();
        result.latenciesUs.push_back(std::chrono::duration<double, std::micro>(t1 - t0).count());
    }
    close(fd);
}
```

Time exactly one round trip: send the request, wait for the full reply.
Encoding is done *before* `t0`, so it's not included. If sending or
receiving fails, stop this thread.

`std::chrono::duration<double, std::micro>(t1 - t0).count()` converts the
time difference into a `double` number of microseconds.

> **C++ note — `!readFrame(fd)`:** `readFrame` returns an `std::optional`,
> which converts to `bool` (`true` if it holds a value). We only care
> whether it succeeded, not about the reply's content.

> **CN refresher — what one "round trip" includes here:** client `write`
> syscall → kernel loopback delivery → server wakes from `poll`, reads,
> processes, queues reply → next `poll`, `write` → kernel delivery →
> client `read` returns. On loopback there's no real network, so the time
> is mostly syscalls, thread scheduling and **waiting in line** behind other
> clients' requests.

---

## Lines 54–60: arguments and deadline

```cpp
int main(int argc, char **argv) {
    int nClients = argc > 1 ? std::atoi(argv[1]) : 200;
    double duration = argc > 2 ? std::atof(argv[2]) : 10.0;

    auto start = Clock::now();
    auto deadline = start + std::chrono::duration_cast<Clock::duration>(
                                std::chrono::duration<double>(duration));
```

- `atoi` / `atof` convert text to `int` / `double`. Defaults: 200 clients, 10 s.
- Every thread gets the **same** deadline, so they all stop together.
- `duration<double>(duration)` is "that many seconds" as a double;
  `duration_cast` converts it to the clock's own tick unit so it can be added
  to a time point.

---

## Lines 62–70: start threads, wait

```cpp
    std::vector<ThreadResult> results(static_cast<size_t>(nClients));
    std::vector<std::thread> threads;
    for (int i = 0; i < nClients; i++) {
        threads.emplace_back(worker, i, deadline, std::ref(results[static_cast<size_t>(i)]));
    }
    for (auto &t : threads) {
        t.join();
    }
    double elapsed = std::chrono::duration<double>(Clock::now() - start).count();
```

1. Create one `ThreadResult` per client **before** starting threads, so the
   vector never reallocates while threads hold references into it.
2. Start each thread running `worker(i, deadline, results[i])`.
3. `join()` waits for each thread to finish.
4. Measure how long the whole test actually took.

> **C++ note — `std::thread`:** `std::thread(f, args...)` starts a new OS
> thread running `f(args...)`. `emplace_back` builds the thread directly
> inside the vector. A `std::thread` must be `join`ed (or detached) before
> it's destroyed, otherwise the program aborts.

> **C++ note — why `std::ref`:** `std::thread` **copies** its arguments by
> default. `worker` takes `ThreadResult &`, and we want it to fill in *our*
> `results[i]`, not a copy. `std::ref(x)` passes a reference wrapper instead.

---

## Lines 72–84: collect results

```cpp
    int failed = 0;
    std::vector<double> all;
    for (const auto &r : results) {
        failed += r.connectFailed;
        all.insert(all.end(), r.latenciesUs.begin(), r.latenciesUs.end());
    }

    printf("clients=%d duration_target=%.1fs actual_wall=%.3fs failed_connects=%d\n",
           nClients, duration, elapsed, failed);
    if (all.empty()) {
        printf("total_ops=0 (no successful requests)\n");
        return failed > 0 ? 1 : 0;
    }
```

Merge every thread's latencies into one big vector, and count failed
connections (`bool` adds as 0 or 1). If nothing succeeded (e.g. the server
isn't running), say so and exit.

> **C++ note — `printf` format codes:** `%d` int, `%.1f` double with 1
> decimal, `%.3f` with 3, `%zu` a `size_t`.

---

## Lines 86–94: statistics

```cpp
    std::sort(all.begin(), all.end());
    auto pct = [&](size_t p) { return all[all.size() * p / 100]; };
    double mean = std::accumulate(all.begin(), all.end(), 0.0) / static_cast<double>(all.size());

    printf("total_ops=%zu throughput=%.1f ops/sec\n", all.size(), static_cast<double>(all.size()) / elapsed);
    printf("latency_us: min=%.1f p50=%.1f p90=%.1f p99=%.1f max=%.1f mean=%.1f\n",
           all.front(), pct(50), pct(90), pct(99), all.back(), mean);
    return 0;
}
```

- **Sort** the latencies, so percentiles are just indexes.
- **`pct(p)`**: the value `p`% of the way through the sorted list. `pct(99)`
  is the latency that 99% of requests beat.
- **`mean`**: the average. `0.0` as the starting value matters: with `0`,
  `accumulate` would add in `int` and truncate.
- **Throughput** = successful requests ÷ elapsed seconds.

> **C++ note — lambda `[&](size_t p) { ... }`:** an inline function.
> `[&]` means it can use local variables (here `all`) by reference.

### How to read the numbers

| Metric | Meaning | Our value |
|---|---|---|
| throughput | Requests completed per second, all clients combined | ~184K ops/s |
| p50 (median) | Half of requests were faster than this | ~1.0 ms |
| p99 | 1 in 100 requests was slower than this ("tail latency") | ~1.9 ms |
| max | The single slowest request | ~21 ms (likely the OS pausing a thread, or a big hashtable allocation) |

Why report percentiles, not just the mean? Because a few very slow requests
hide inside an average. If a web page makes 100 database calls, it will
almost always hit one p99-slow call, so tail latency is what users feel.

> **CN refresher — Little's law, sanity-checking the benchmark:** in a
> closed loop, `clients = throughput × latency`. Check:
> `184,000/s × 1.08 ms ≈ 199` ✓. So with 200 clients, latency is about
> `200 / 184,000 s ≈ 1.1 ms`. Most of that is **queueing**: each request
> waits for the others ahead of it on the single server thread. Fewer
> clients would mean lower latency; the server's cost per request is only
> about 1 / 184,000 s ≈ 5 µs.

### Caveats worth knowing

- The server, the 200 client threads and the OS all share the same machine,
  so the clients steal CPU from the server. Real deployments put them on
  different machines.
- Loopback has no real network latency. Over a real network, each request
  would add the network round-trip time (~0.1–1 ms in a data centre).
- Values are tiny (`v123`), so this measures per-request overhead, not
  bandwidth.
