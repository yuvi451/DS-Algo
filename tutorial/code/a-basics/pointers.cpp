#include <iostream>
using namespace std;

// Takes a reference: changes made here are visible to the caller.
void addTen(int &x) {
    x += 10;
}

struct Node {
    int val;
    Node *next;  // the next node in the list, or nullptr at the end
};

int main() {
    int score = 5;
    int *p = &score;  // p holds the address of score
    *p = 7;           // change score through p
    cout << "score: " << score << endl;

    addTen(score);
    cout << "after addTen: " << score << endl;

    // A linked list: 1 -> 2 -> 3, built with new.
    Node *head = new Node{1, nullptr};
    head->next = new Node{2, nullptr};
    head->next->next = new Node{3, nullptr};

    cout << "list:";
    for (Node *n = head; n != nullptr; n = n->next) cout << " " << n->val;
    cout << endl;

    // Remove the middle node: make 1 point past it, then free it.
    Node *middle = head->next;
    head->next = middle->next;
    delete middle;

    cout << "after removing 2:";
    for (Node *n = head; n != nullptr; n = n->next) cout << " " << n->val;
    cout << endl;
    return 0;
}
