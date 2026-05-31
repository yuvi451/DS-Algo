#include <bits/stdc++.h>
using namespace std;
#pragma GCC optimize("O3,unroll-loops")

#define ll long long
#define forl(i, a, b) for(ll i = a; i < b; i++)
#define rfor(i, a, b) for(ll i = a; i > b; i--)
#define fora(x, v) for(auto &x : v)
#define vl vector<ll>
#define vvl vector<vector<ll>>
#define pr pair<ll,ll>
#define pb push_back
#define vpr vector<pair<ll,ll>>
#define all(v) v.begin(), v.end()

const ll inf = 1e13;
const ll mod = 1e9 + 7;
const ll N = 2e5 + 5;

class Node{
    public:
    int data;
    Node* next;
    Node* bottom;

    Node(int data1){
        data = data1;
        next = nullptr;
        bottom = nullptr;
    }
};

Node* ArrayToLL(vector<int> &arr){
    Node* head = new Node(arr[0]);
    Node* temp = head;  // do not tamper with head
    for(int i = 1; i < arr.size(); i++){
        Node* newNode = new Node(arr[i]);
        temp->bottom = newNode;
        temp = newNode;
    }
    return head;
}

void PrintLL(Node* head){
    Node* temp = head;
    while (temp){
        cout<<temp->data<<" ";
        temp = temp->bottom;
    }
    cout<<'\n';
}

Node* merge(Node* head1, Node* head2){
    Node* head = new Node(0);
    Node* temp = head;
    while (head1 && head2){
        if (head1->data < head2->data){
            Node* bottom = head1->bottom;
            head1->bottom = NULL;
            temp->bottom = head1;
            head1 = bottom;
        } else {
            Node* bottom = head2->bottom;
            head2->bottom = NULL;
            temp->bottom = head2;
            head2 = bottom;
        }
        temp = temp->bottom;
    }
    while (head1){
        Node* bottom = head1->bottom;
        head1->bottom = NULL;
        temp->bottom = head1;
        head1 = bottom;
        temp = temp->bottom;
    }
    while (head2){
        Node* bottom = head2->bottom;
        head2->bottom = NULL;
        temp->bottom = head2;
        head2 = bottom;
        temp = temp->bottom;
    }
    return head->bottom;
}

Node* FlattenLL(Node* head, Node* tail){
    if (head == NULL || head->next == NULL) return head;

    Node* slow = head;
    Node* fast = head;
    Node* prev = NULL;

    while (fast && fast->next){
        fast = fast->next->next;
        prev = slow;
        slow = slow->next;
    }

    prev->next = NULL; // Very IMP 

    Node* head1 = FlattenLL(head, prev);
    Node* head2 = FlattenLL(slow, fast);
    return merge(head1, head2);
}

int main(){
    ios::sync_with_stdio(0);
    cin.tie(0);
    vector<int>arr1 = {5, 7, 8};
    vector<int>arr2 = {10, 20};
    vector<int>arr3 = {19, 20};
    vector<int>arr4 = {28, 40, 45};

    Node* head1 = ArrayToLL(arr1);
    Node* head2 = ArrayToLL(arr2);
    Node* head3 = ArrayToLL(arr3);
    Node* head4 = ArrayToLL(arr4);

    head1->next = head2;
    head2->next = head3;
    head3->next = head4;

    Node* head = FlattenLL(head1, head4);
    PrintLL(head);
    return 0;
}
