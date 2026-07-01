#include <iostream>
#include <bits/stdc++.h>
using namespace std;

class Node{
    public:
    int data;
    Node* left;
    Node* right;
    Node(int value){
        data = value;
        left = NULL;
        right = NULL;
    }
};

vector<int>inorder(Node* root){
    vector<int>v;
    Node* curr = root;
    stack<Node*>st;

    while (curr != NULL || !st.empty()){
        while (curr != NULL){
            st.push(curr);
            curr = curr->left;
        }
        curr = st.top();
        st.pop();
        v.push_back(curr->data);

        curr = curr->right;
    }
    return v;
}

Node* inorderToBST(vector<int>&inorder, int low, int high){
    if (low > high) return NULL;
    
    int mid = (low + high)/2;
    Node* root = new Node(inorder[mid]);

    root->left = inorderToBST(inorder, low, mid - 1);
    root->right = inorderToBST(inorder, mid + 1, high);

    return root;
}

int main(){
    ios::sync_with_stdio(0);
    cin.tie(0);

    Node* root1 = new Node(6);
    root1->left = new Node(2);
    root1->right = new Node(8);
    root1->right->left = new Node(7);
    root1->right->right = new Node(9);

    Node* root2 = new Node(8);
    root2->left = new Node(3);
    root2->right = new Node(10);
    root2->left->left = new Node(1);
    root2->left->right = new Node(6);
    root2->right->right = new Node(14);
    root2->left->right->left = new Node(4);
    root2->left->right->right = new Node(7);
    root2->right->right->left = new Node(13);

    vector<int>v1 = inorder(root1);     // O(N)
    vector<int>v2 = inorder(root2);     // O(M)
    vector<int>combinedInorder;

    // O(N + M)
    int left = 0, right = 0;
    while (left < v1.size() && right < v2.size()){
        if (v1[left] <= v2[right]){
            combinedInorder.push_back(v1[left]);
            left++;
        } else {
            combinedInorder.push_back(v2[right]);
            right++;
        }
    }
    while (left < v1.size()){
        combinedInorder.push_back(v1[left]);
        left++;
    }
    while(right < v2.size()){
        combinedInorder.push_back(v2[right]);
        right++;
    }

    // O(N + M)
    int n = combinedInorder.size();
    Node* root = inorderToBST(combinedInorder, 0, n - 1);
    vector<int>v3 = inorder(root);

    // Total time complexity: O(N + M)

    if (v3 == combinedInorder) cout<<"YES";

    return 0;
}
