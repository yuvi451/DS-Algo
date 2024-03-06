#include <bits/stdc++.h>
using namespace std;
void f(vector <int> input_set, vector <int> subset, int i){
    if (i == input_set.size()){
        for (auto it:subset){
            cout<<it<<" ";
        } cout<<endl;
    } else {
        subset.push_back(input_set[i]);
        f(input_set, subset, i+1);
        subset.pop_back();
        f(input_set, subset, i+1);
    }
}
int main(){
    vector <int> input_set = {1,2,3,4};
    vector <int> subset;
    f(input_set, subset, 0);
    return 0;
}