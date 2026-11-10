#include <iostream>

#include "../src/hashtable.h"
using namespace std;

void show(const string &s) {
    uint64_t h = hashString(s);
    cout << "hash(\"" << s << "\") = " << h << "  -> bucket " << (h & 7) << " of 8" << endl;
}

int main() {
    show("");
    show("a");
    show("foo");
    show("fop");
    return 0;
}
