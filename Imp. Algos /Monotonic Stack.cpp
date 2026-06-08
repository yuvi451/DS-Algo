#include <iostream>
#include <bits/stdc++.h>
using namespace std;

void NSE(vector<int>&arr, vector<int>&nse){
    stack<int>st;
    int n = arr.size();
    for(int i = n - 1; i >= 0; i--){
        while (!st.empty() && arr[st.top()] >= arr[i]){
            st.pop();
        }
        if (st.empty()){
            nse[i] = n;
        } else {
            nse[i] = st.top();
        }
        st.push(i);
    }
}

void PSE(vector<int>&arr, vector<int>&pse){
    stack<int>st;
    int n = arr.size();
    for(int i = 0; i < n; i++){
        while (!st.empty() && arr[st.top()] >= arr[i]){
            st.pop();
        }
        if (st.empty()){
            pse[i] = -1;
        } else {
            pse[i] = st.top();
        }
        st.push(i);
    }
}

void NGE(vector<int>&arr, vector<int>&nge){
    stack<int>st;
    int n = arr.size();
    for(int i = n - 1; i >= 0; i--){
        while (!st.empty() && arr[st.top()] <= arr[i]){
            st.pop();
        }
        if (st.empty()){
            nge[i] = n;
        } else {
            nge[i] = st.top();
        }
        st.push(i);
    }
}

void PGE(vector<int>&arr, vector<int>&pge){
    stack<int>st;
    int n = arr.size();
    for(int i = 0; i < n; i++){
        while (!st.empty() && arr[st.top()] <= arr[i]){
            st.pop();
        }
        if (st.empty()){
            pge[i] = -1;
        } else {
            pge[i] = st.top();
        }
        st.push(i);
    }
}

int main() {
    vector<int>arr = {12, 32, 1, 2, 33, 6, 66, 78, 10};
    vector<int>nge(arr.size());
    NGE(arr, nge);
    for(int i = 0; i < arr.size(); i++){
        cout<<arr[i]<<" "<<(nge[i] == arr.size() ? -1: arr[nge[i]])<<'\n';
    }
    return 0;
}
