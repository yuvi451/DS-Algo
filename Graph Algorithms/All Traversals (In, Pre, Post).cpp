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
    Node* left;
    Node* right;
    Node(int value){
        data = value;
        left = NULL;
        right = NULL;
    }
};

void inOrderTraversal(Node* root){
    // left -> root -> right
    if (root == NULL) return;

    inOrderTraversal(root->left);   // traverses/prints the entire left subtree
    cout<<root->data<<" ";  // prints the current root node
    inOrderTraversal(root->right);  // traverses/prints the entire right subtree  

    // 17 241 0 8 429 11 3 320 2 401  616 1 257 8 241 17
}

void preOrderTraversal(Node* root){
    // root -> left -> right
    if (root == NULL) return;

    cout<<root->data<<" ";  // prints root
    preOrderTraversal(root->left);  // prints left subtree
    preOrderTraversal(root->right);    // prints right subtree

    // 320 8 241 17 0 429 3 11 8 2 1 401 616 257 241 17
}

void postOrderTraversal(Node* root){
    // left -> right -> root
    if (root == NULL) return;

    postOrderTraversal(root->left);     // prints left subtree
    postOrderTraversal(root->right);    // prints right subtree
    cout<<root->data<<" ";      // prints root

    // 17 0 241 11 3 429 8 616 401 257 1 2 17 241 8 320
}

void allTraversals(Node* root) {
    vector<int>preorder, inorder, postorder;
    stack<pair<Node*, int>>st;
    st.push({root, 1});

    while(!st.empty()){
        auto it = st.top();
        st.pop();

        if (it.second == 1){
            preorder.push_back(it.first->data);

            it.second = 2;
            st.push(it);

            if (it.first->left != NULL){
                st.push({it.first->left, 1});
            }
        } else if (it.second == 2){
            inorder.push_back(it.first->data);

            it.second = 3;
            st.push(it);

            if (it.first->right != NULL){
                st.push({it.first->right, 1});
            }
        } else {
            postorder.push_back(it.first->data);
        }
    }
    for(auto it: preorder) cout<<it<<" ";
    cout<<'\n';
    for(auto it: inorder) cout<<it<<" ";
    cout<<'\n';
    for(auto it: postorder) cout<<it<<" ";
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

    inOrderTraversal(root);
    cout<<'\n';
    preOrderTraversal(root);
    cout<<'\n';
    postOrderTraversal(root);
    return 0;
}
