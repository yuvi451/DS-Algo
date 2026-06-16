#include <iostream>
#include <bits/stdc++.h>
using namespace std;

void merge(vector<pair<int, int>>&arr, vector<int>&NumGreaterRight, int low, int mid, int high){
    int left = low, right = mid + 1;
    vector<pair<int, int>>temp;
    while (left <= mid && right <= high){
        if (arr[left].first < arr[right].first){
            NumGreaterRight[arr[left].second] += (high - right + 1);
            temp.push_back(arr[left]);
            left++;
        } else {
            temp.push_back(arr[right]);
            right++;
        }
    }

    while (left <= mid){
        temp.push_back(arr[left]);
        left++;
    }

    while (right <= high){
        temp.push_back(arr[right]);
        right++;
    }

    for(int i = low; i <= high; i++){
        arr[i] = temp[i - low];
    }
}

void merge_sort(vector<pair<int, int>>&arr, vector<int>&NumGreaterRight, int low, int high){
    if (low < high){
        int mid = (low + high)/2;

        merge_sort(arr, NumGreaterRight, low, mid);
        merge_sort(arr, NumGreaterRight, mid + 1, high);
        merge(arr, NumGreaterRight, low, mid, high);
    }
}

int main() {
    vector<int>v = {-78, -2, 0, 99, 23, 2, 30, 3, 85, -101};
    int n = v.size();
    vector<pair<int, int>>arr;
    for(int i = 0; i < n; i++) arr.push_back({v[i], i}); 
    vector<int>NumGreaterRight(n);
    merge_sort(arr, NumGreaterRight, 0, n - 1);
    for(int i = 0; i < n; i++){
        cout<<v[i]<<" "<<NumGreaterRight[i]<<'\n';
    }
    return 0;
}
