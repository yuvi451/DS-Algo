#include <cstdint>
#include <iostream>
#include <string>
using namespace std;

int main() {
    cout << "uint32_t: " << sizeof(uint32_t) << " bytes" << endl;
    cout << "uint64_t: " << sizeof(uint64_t) << " bytes" << endl;

    uint32_t v = 0x01020304;
    string bytes((char *)&v, 4);  // copy the 4 raw bytes of v into a string
    cout << "bytes in memory:";
    for (char b : bytes) cout << " " << (int)b;
    cout << endl;

    uint32_t back;
    bytes.copy((char *)&back, 4);  // and copy them back into a number
    cout << "read back: " << back << " (same as " << v << ")" << endl;
    return 0;
}
