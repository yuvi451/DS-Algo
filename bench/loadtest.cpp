#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <unistd.h>

#include "../src/protocol.h"

using Clock = std::chrono::steady_clock;

struct ThreadResult {
    long opsDone = 0;
    std::vector<double> latenciesUs;
    bool connectFailed = false;
};

static int connectServer() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        return -1;
    }
    int one = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));

    struct sockaddr_in addr {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(SERVER_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (connect(fd, reinterpret_cast<struct sockaddr *>(&addr), sizeof(addr)) != 0) {
        close(fd);
        return -1;
    }
    return fd;
}

static void worker(int threadId, double durationSec, ThreadResult &result) {
    int fd = connectServer();
    if (fd < 0) {
        result.connectFailed = true;
        return;
    }

    long counter = 0;
    auto tEnd = Clock::now() + std::chrono::duration_cast<Clock::duration>(
                                   std::chrono::duration<double>(durationSec));

    while (Clock::now() < tEnd) {
        bool isSet = (counter % 2 == 0);
        std::string key = "lt:" + std::to_string(threadId) + ":" + std::to_string(counter / 2);

        std::vector<std::string> args;
        if (isSet) {
            args = {"set", key, "v" + std::to_string(counter)};
        } else {
            args = {"get", key};
        }

        Buffer req;
        encodeRequest(req, args);

        auto t0 = Clock::now();
        if (!writeFrame(fd, req.data(), req.size())) {
            break;
        }
        auto resp = readFrame(fd);
        if (!resp) {
            break;
        }
        auto t1 = Clock::now();

        parseResponse(resp->data() + 4, resp->size() - 4);

        double us = std::chrono::duration<double, std::micro>(t1 - t0).count();
        result.latenciesUs.push_back(us);
        result.opsDone++;
        counter++;
    }

    close(fd);
}

int main(int argc, char **argv) {
    int nClients = argc > 1 ? std::atoi(argv[1]) : 200;
    double duration = argc > 2 ? std::atof(argv[2]) : 10.0;

    std::vector<std::thread> threads;
    std::vector<ThreadResult> results(static_cast<size_t>(nClients));

    auto tStart = Clock::now();
    for (int i = 0; i < nClients; i++) {
        threads.emplace_back(worker, i, duration, std::ref(results[static_cast<size_t>(i)]));
    }
    for (auto &t : threads) {
        t.join();
    }
    double elapsed = std::chrono::duration<double>(Clock::now() - tStart).count();

    long totalOps = 0;
    int failed = 0;
    std::vector<double> all;
    for (auto &r : results) {
        if (r.connectFailed) {
            failed++;
        }
        totalOps += r.opsDone;
        all.insert(all.end(), r.latenciesUs.begin(), r.latenciesUs.end());
    }

    printf("clients=%d duration_target=%.1fs actual_wall=%.3fs failed_connects=%d\n",
           nClients, duration, elapsed, failed);

    if (all.empty()) {
        printf("total_ops=0 (no successful requests)\n");
        return failed > 0 ? 1 : 0;
    }

    std::sort(all.begin(), all.end());
    double sum = 0;
    for (double v : all) {
        sum += v;
    }

    printf("total_ops=%ld throughput=%.1f ops/sec\n", totalOps, static_cast<double>(totalOps) / elapsed);
    printf("latency_us: min=%.1f p50=%.1f p90=%.1f p99=%.1f max=%.1f mean=%.1f\n",
           all.front(),
           all[all.size() * 50 / 100],
           all[all.size() * 90 / 100],
           all[all.size() * 99 / 100],
           all.back(),
           sum / static_cast<double>(all.size()));

    return 0;
}
