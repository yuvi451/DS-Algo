#include <bits/stdc++.h>
using namespace std;
int main(){
    int arr[8]={-1,2,4,-3,5,2,-5,2};
    int max_subarr_sum=0;
    int sum=0;
    for (int i=0; i<8; i++){
        sum = max(arr[i], sum+arr[i]);
        max_subarr_sum = max(sum, max_subarr_sum);
    }
    cout<<max_subarr_sum;
    return 0;
}