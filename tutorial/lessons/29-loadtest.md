---
title: How fast is it? A multi-threaded load tester
module: Ship it
time: 50 min
---

:::goal
Measure the server like a real engineer: **throughput** (requests per
second) and **latency percentiles** (p50, p99). Write `bench/loadtest.cpp`,
which runs N threads, each with its own connection, alternating `set`/`get`
and timing every round trip. You'll learn how to run threads and measure
time.
:::

## Throughput vs latency

| Metric | Question it answers | Unit |
|---|---|---|
| **Throughput** | How much work per second can the server do? | ops/sec |
| **Latency** | How long does *one* request take, start to finish? | µs (microseconds) |

Averages lie about latency. If 99 requests take 1 ms and one takes 1 second,
the mean is ~11 ms, which describes *none* of them. So we report
**percentiles**: **p50** (the median: half of requests were faster), **p90**,
**p99** (only 1% were slower) and **max**. Redis cares deeply about p99
and max. That's the whole reason for progressive rehashing.

## Closed-loop clients

Each client thread does: send a request → **wait** for the reply → send the
next. That's a *closed loop*. With 200 threads there are at most 200 requests
in flight at once.

## New C++ features

:::cpp Measuring time
The load tester needs one helper that tells the time in microseconds:

```cpp
// Microseconds since some fixed moment. Only differences between two calls matter.
double nowUs() {
    return chrono::duration<double, micro>(chrono::steady_clock::now().time_since_epoch()).count();
}
```

The inside is long-winded standard-library code (`<chrono>`), but you only
use it like this:

```cpp
double start = nowUs();
/* ... one request ... */
double took = nowUs() - start;   // microseconds
```

`steady_clock` is a clock that never jumps backwards, which is what you want
for measuring durations.
:::

:::cpp `thread`: running functions at the same time
```cpp
vector<thread> threads;
threads.push_back(thread(worker, i, endUs, &results[i]));   // starts worker(i, endUs, &results[i])
for (thread &t : threads) t.join();                          // wait for every thread to finish
```
- `thread(function, args...)` starts running `function(args...)` **in
  parallel** with the rest of the program.
- We pass `&results[i]`, a pointer, so each worker writes into *its own*
  `Result`.
- Each thread writes only to its own `Result`, so no locks are needed.
  Results are combined only after every `join()`.
- Compile with `-pthread` to turn on thread support.
:::

## The program

@include ../bench/loadtest.cpp

Highlights:

- `argc > 1 ? stoi(argv[1]) : 200`: an optional command-line argument with a
  default. `stoi`/`stod` convert text to `int`/`double`. (`cond ? a : b` is a
  one-line if/else: `a` if `cond` is true, otherwise `b`.)
- Each worker uses its own keys (`lt:<thread>:<n>`), `set` on even `i`, `get`
  of the same key on odd `i`.
- `writeFrame` + `readFrame` are the blocking helpers from Part 4. The time
  between `start` and the end is one full round trip.
- After joining, all latencies are merged, **sorted**, and percentiles are
  read off by position: p50 is `all[n * 50 / 100]`.
- `cout << fixed << setprecision(1)` (from `<iomanip>`) prints every decimal
  number with exactly one digit after the point.

:::task Benchmark your server
1. Create `bench/loadtest.cpp` (the include path is `"../src/protocol.h"`).
2. Build and run. The server must be the **release** build (`-O2`):

```bash
$ make all bench
$ build/server &
$ build/loadtest 200 10
$ kill %1
```

`build/server &` runs the server in the background of the same terminal;
`kill %1` stops it afterwards. (Or use two terminals as usual.)
:::

```output
clients=200 duration_target=10.0s actual_wall=10.0xxs failed_connects=0
total_ops=… throughput=~180000 ops/sec
latency_us: min=… p50=~1000 p90=… p99=~2000 max=… mean=…
```

Your numbers depend on your machine. The project's README records
**~184,000 ops/sec, p50 ≈ 1.0 ms, p99 ≈ 1.9 ms** on an Apple M2 laptop over
loopback, all from **one** server thread.

:::why Why is p50 about 1 ms when a single request is much faster?
200 clients share one server thread. When your request arrives, it waits its
turn behind the others in the same `poll()` round. Latency ≈ (clients in
flight) ÷ (throughput) = 200 ÷ 184,000 ≈ 1.1 ms. That's **Little's law**.
Try `build/loadtest 10 5` and watch p50 drop.
:::

:::quiz Experiment: what happens to throughput with 1 client vs 200?
With 1 client, throughput is limited by the round-trip time of **one**
request at a time, so it's far lower. More clients keep the server busy
(several requests per `poll()` round) until it saturates the single thread.
After that, more clients mostly add latency, not throughput.
:::

:::recap
- Report throughput **and** latency percentiles. Averages hide tail latency.
- `nowUs()` for timing, `thread` + `join` for parallel clients, each writing to its own `Result`.
- One thread per client, each with private results, means no locks.
:::
