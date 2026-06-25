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

void preorder(Node* root){
    if (root == NULL) return;

    stack<Node*>st;
    st.push(root);
    while (!st.empty()){
        Node* node = st.top();
        st.pop();

        cout<<node->data<<" ";
        // push right child first so that left child can be processed first 
        // stack LIFO
        if (node->right) st.push(node->right);
        if (node->left) st.push(node->left);
    }
}

void inorder(Node* root){
    if (root == NULL) return;

    stack<Node*>st;
    Node* curr = root;
    while (curr != NULL || !st.empty()){
        while (curr != NULL){
            st.push(curr);
            curr = curr->left;
        }
        // if curr == NULL means left node / left subtree of st.top() has been processed so we move to the root
        // left -> root -> right
        curr = st.top();    // root
        st.pop();
        cout<<curr->data<<" ";

        curr = curr->right;    // right
    }

    // the logic is: process left subtree -> print root -> go to right node : repeat
}

void postorder_2stack(Node* root) {
    if (root == NULL) return;

    // preorder: root -> left -> right
    // slightly modify it: root -> right -> left [easily doable by changing the order of if(node->right) & if(node->left)]
    // now reverse it (putting in another stack and then printng does it): voila !!

    stack<Node*>st1, st2;
    st1.push(root);
    while (!st1.empty()){
        Node* node = st1.top();
        st1.pop();

        st2.push(node);

        // push left first so that right is processed first
        if (node->left) st1.push(node->left);
        if (node->right) st1.push(node->right);
    }

    while (!st2.empty()){
        cout<<st2.top()->data<<" ";
        st2.pop();
    }
}

void postorder_1stack(Node* root){
    if (root == NULL) return;

    stack<Node*>st;
    Node* curr = root;
    Node* last_visited_node = NULL;
    while(curr != NULL || !st.empty()){
        while (curr != NULL){
            st.push(curr);
            curr = curr->left;
        }

        // if curr == NULL then left subtree of st.top() has been processed so we move to the root;
        curr = st.top();    // root
        // before doing anyhting we first check if the right subtree has been processed or not
        if (curr->right != NULL && curr->right != last_visited_node){
            // if right subtree has not been processed
            curr = curr->right;
        } else {
            // if curr->right == NULL means both left and right subtree of st.top() have been processed so we print root i.e. stack.top()
            // or if curr->right == last_visited_node means both left and right subtree of st.top() have been processed so we print root i.e. stack.top()
            cout<<curr->data<<" ";
            last_visited_node = curr;
            st.pop();

            curr = NULL;    // important thing !! coz we're done with curr node
        }
    }
}

int main(){
    ios::sync_with_stdio(0);
    cin.tie(0);
    Node* root = new Node(320);
    root->left = new Node(8);       
    root->right = new Node(8);       
    root->left->left = new Node(241);    
    root->left->right = new Node(429);   
    root->left->left->left = new Node(17);  
    root->left->left->right = new Node(0);   
    root->left->right->right = new Node(3);  
    root->left->right->right->left = new Node(11); 
    root->right->left = new Node(2);     
    root->right->right = new Node(241); 
    root->right->left->right = new Node(1); 
    root->right->left->right->left = new Node(401);  
    root->right->left->right->right = new Node(257); 
    root->right->left->right->left->right = new Node(616); 
    root->right->right->right = new Node(17); 
    
    postorder_2stack(root); cout<<'\n';
    postorder_1stack(root);
    return 0;
}
