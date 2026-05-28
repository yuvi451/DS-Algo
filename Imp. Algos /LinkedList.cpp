#include <iostream>
#include <bits/stdc++.h>
using namespace std;

class Node {
    public:
    int data;
    Node* next;
    Node* back;

    Node(int data1, Node* next1, Node* back1){
        data = data1;
        next = next1;
        back = back1;
    }

    Node(int data1){
        data = data1;
        next = nullptr;
        back = nullptr;
    }
};

Node* ArrayToLL(vector<int> &v){
    Node* head = new Node(v[0]);
    Node* prev = head;
    for(int i = 1; i < v.size(); i++){
        Node* temp = new Node(v[i]);
        prev->next = temp;
        temp->back = prev;
        prev = temp;

    }
    return head;
};

void Traversal(Node* head){
    Node* temp = head;
    while (temp){
        cout<<temp->data<<" ";
        temp = temp->next;
    }
};

Node* RemoveHead(Node* head){
    if (head == nullptr || head->next == nullptr) return nullptr;

    Node* prev = head;
    head = head->next;
    head->back = nullptr;
    prev->next = nullptr;
    delete prev;
    return head;
};

Node* DeleteTail(Node* head){
    if (head == nullptr || head->next == nullptr) {
        delete head;
        return nullptr;
    }

    Node* tail = head;
    while (tail->next != nullptr){
        tail = tail->next;
    }
    tail->back->next = nullptr;
    tail->back = nullptr;
    delete tail;
    return head;
}

Node* DeleteKthElement(Node* head, int K){
    int cnt = 0; 
    Node* temp = head;
    while (temp){
        cnt++;
        if (cnt == K) break;
        temp = temp->next;
    }

    Node* front = temp->next;
    Node* prev = temp->back;

    // prev    temp  front

    if (prev == nullptr && front == nullptr){
        delete head;
        return nullptr;
    } else if (prev == nullptr){
        front->back = nullptr;
        temp->next = nullptr;
        delete temp;
        return front;
    } else if (front == nullptr) {
        prev->next = nullptr;
        temp->back = nullptr;
        delete temp;
        return head;
    }

    prev->next = front;
    front->back = prev;

    temp->next = nullptr;
    temp->back = nullptr;

    delete temp;
    return head;
}

int main() {
    vector<int>v = {1, 2, 3, 4, 5};
    Node* head = ArrayToLL(v);
    head = DeleteKthElement(head, 2);
    Traversal(head);
    return 0;
}
