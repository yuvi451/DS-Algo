// Load test: N threads, one connection each, alternating set/get and timing
// every round trip.
//
// usage: loadtest [clients=200] [seconds=10]

#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

#include <unistd.h>

#include "../src/protocol.h"
using namespace std;

// Microseconds since some fixed moment. Only differences between two calls matter.
double nowUs() {
    return chrono::duration<double, micro>(chrono::steady_clock::now().time_since_epoch()).count();
}

struct Result {
    vector<double> latencies;  // microseconds, one per request
    bool connectFailed = false;
};

// Runs in its own thread. Only writes to its own Result, so no locks needed.
void worker(int id, double endUs, Result *result) {
    int fd = connectToServer();
    if (fd < 0) {
        result->connectFailed = true;
        return;
    }
    for (int i = 0; nowUs() < endUs; i++) {
        string key = "lt:" + to_string(id) + ":" + to_string(i / 2);
        string request;
        if (i % 2 == 0) {
            request = encodeRequest({"set", key, "v" + to_string(i)});
        } else {
            request = encodeRequest({"get", key});
        }

        double start = nowUs();
        string reply;
        if (!writeFrame(fd, request) || !readFrame(fd, reply)) break;
        result->latencies.push_back(nowUs() - start);
    }
    close(fd);
}

int main(int argc, char **argv) {
    int clients = argc > 1 ? stoi(argv[1]) : 200;
    double seconds = argc > 2 ? stod(argv[2]) : 10;

    double startUs = nowUs();
    double endUs = startUs + seconds * 1e6;

    vector<Result> results(clients);
    vector<thread> threads;
    for (int i = 0; i < clients; i++) {
        threads.push_back(thread(worker, i, endUs, &results[i]));
    }
    for (thread &t : threads) t.join();  // wait for every thread to finish
    double elapsed = (nowUs() - startUs) / 1e6;

    int failed = 0;
    vector<double> all;
    for (Result &r : results) {
        if (r.connectFailed) failed++;
        for (double us : r.latencies) all.push_back(us);
    }

    cout << fixed << setprecision(1);  // print doubles with 1 decimal place
    cout << "clients=" << clients << " duration_target=" << seconds << "s actual_wall="
         << elapsed << "s failed_connects=" << failed << endl;
    if (all.empty()) {
        cout << "total_ops=0 (no successful requests)" << endl;
        return failed > 0 ? 1 : 0;
    }

    sort(all.begin(), all.end());
    double sum = 0;
    for (double us : all) sum += us;
    size_t n = all.size();

    cout << "total_ops=" << n << " throughput=" << n / elapsed << " ops/sec" << endl;
    cout << "latency_us: min=" << all[0] << " p50=" << all[n * 50 / 100] << " p90=" << all[n * 90 / 100]
         << " p99=" << all[n * 99 / 100] << " max=" << all[n - 1] << " mean=" << sum / n << endl;
    return 0;
}
