// Closed-loop load test: N threads, one connection each, alternating set/get
// and timing every round trip.
//
// usage: loadtest [n_clients=200] [duration_sec=10]

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <numeric>
#include <string>
#include <thread>
#include <vector>

#include <unistd.h>

#include "../src/protocol.h"

using Clock = std::chrono::steady_clock;

struct ThreadResult {
    std::vector<double> latenciesUs;
    bool connectFailed = false;
};

static void worker(int threadId, Clock::time_point deadline, ThreadResult &result) {
    int fd = connectToServer();
    if (fd < 0) {
        result.connectFailed = true;
        return;
    }

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

        auto t0 = Clock::now();
        if (!writeFrame(fd, request) || !readFrame(fd)) {
            break;
        }
        auto t1 = Clock::now();
        result.latenciesUs.push_back(std::chrono::duration<double, std::micro>(t1 - t0).count());
    }
    close(fd);
}

int main(int argc, char **argv) {
    int nClients = argc > 1 ? std::atoi(argv[1]) : 200;
    double duration = argc > 2 ? std::atof(argv[2]) : 10.0;

    auto start = Clock::now();
    auto deadline = start + std::chrono::duration_cast<Clock::duration>(
                                std::chrono::duration<double>(duration));

    std::vector<ThreadResult> results(static_cast<size_t>(nClients));
    std::vector<std::thread> threads;
    for (int i = 0; i < nClients; i++) {
        threads.emplace_back(worker, i, deadline, std::ref(results[static_cast<size_t>(i)]));
    }
    for (auto &t : threads) {
        t.join();
    }
    double elapsed = std::chrono::duration<double>(Clock::now() - start).count();

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

    std::sort(all.begin(), all.end());
    auto pct = [&](size_t p) { return all[all.size() * p / 100]; };
    double mean = std::accumulate(all.begin(), all.end(), 0.0) / static_cast<double>(all.size());

    printf("total_ops=%zu throughput=%.1f ops/sec\n", all.size(), static_cast<double>(all.size()) / elapsed);
    printf("latency_us: min=%.1f p50=%.1f p90=%.1f p99=%.1f max=%.1f mean=%.1f\n",
           all.front(), pct(50), pct(90), pct(99), all.back(), mean);
    return 0;
}
