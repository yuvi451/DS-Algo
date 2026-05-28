#include <iostream>
#include <bits/stdc++.h>
using namespace std;

class Node {
    public:
    Node* next;
    int data;

    Node(int data1, Node* next1){
        next = next1;
        data = data1;
    }

    Node(int data1){
        data = data1;
        next = nullptr;
    }
};

Node* ArrayToLL(vector<int> &arr){
    Node* head = new Node(arr[0]);
    Node* temp = head;  // do not tamper with head
    for(int i = 1; i < arr.size(); i++){
        Node* newNode = new Node(arr[i]);
        temp->next = newNode;
        temp = newNode;
    }
    return head;
}

void PrintLL(Node* head){
    Node* temp = head;
    while (temp){
        cout<<temp->data<<" ";
        temp = temp->next;
    }
    cout<<'\n';
}

Node* reverseLL(Node* head) {
    Node* curr = head;
    Node* prev = nullptr;
    while (curr){
        Node* next = curr->next;
        curr->next = prev;
        prev = curr;
        if (next == nullptr) break;
        curr = next;
    }
    return curr;
}

Node* RemoveKthElement(Node* head, int K){
    if (head == nullptr) return head;

    Node* temp = head;
    Node* prev = nullptr;
    int cnt = 0;
    while (temp){
        cnt++;
        if (cnt == K) break;
        prev = temp;
        temp = temp->next;
    }

    if (K < 1 || K > cnt) return head;
    // remove head
    if (K == 1){
        Node* t = head;
        head = head->next;
        delete t;
        return head;
    } else if (temp->next == nullptr){
        // remove tail
        prev->next = nullptr;
        delete temp;
        // delete a node only after its completely detached
        return head;
    } else {
        Node* back = prev;
        Node* front = temp->next;
        Node* curr = temp;

        curr->next = nullptr;
        back->next = front;
        delete curr;
        return head;
    }
}

Node* InsertAfterKthNode(Node* head, int K, int data){
    if (head == nullptr){
        return new Node(data);
    }
    
    Node* temp = head;
    int cnt = 0;
    while (temp){
        cnt++;
        if (cnt == K) break;
        temp = temp->next;
    }

    // K == 0 means before head
    if (K > cnt) return head;

    Node* newNode = new Node(data);

    if (K == 0){
        newNode->next = head;
        return newNode;
    } else if (temp->next == nullptr){
        temp->next = newNode;
    } else {
        Node* back = temp;
        Node* front = temp->next;

        back->next = newNode;
        newNode->next = front;
    }
    return head;
}   

int main() {
    vector<int> arr = {12, 1, 4, 5, 8, 9, 19};
    Node* head = ArrayToLL(arr);
    Node* h = InsertAfterKthNode(head, 7, 45);
    Node* p = RemoveKthElement(h, 8);
    PrintLL(p);
    return 0;
}
