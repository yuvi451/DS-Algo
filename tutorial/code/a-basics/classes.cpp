#include <iostream>
#include <string>
using namespace std;

struct Counter {
    string name;
    int count = 0;  // every new Counter starts at 0

    void add() { count++; }
    void print() { cout << name << ": " << count << endl; }
};

int main() {
    Counter a;
    a.name = "a";
    a.add();
    a.add();
    a.print();

    Counter *b = new Counter();  // lives until we delete it
    b->name = "b";
    b->add();
    b->print();
    delete b;
    return 0;
}
