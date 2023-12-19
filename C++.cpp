#include <iostream>
#include <bits/stdc++.h>
using namespace std;
int main(){
    int t;
    cin>>t;
    while(t>0){
        int n;
        string s;
        cin>>n>>s;
        int x=-1;
        int y=-1;
        int k=0;
        for (int i=0; i<n; i++){
            if (s[i]=='A'){
                k++;
                if (k==1){
                    x=i;
                }
            } else if (s[i]=='B'){
                y=i;
            }
        }
        if (x==-1 or y==-1){
            cout<<0<<endl;
        }else if (x>y){
            cout<<0<<endl;
        } else if (y>x){
            cout<<y-x<<endl;
        }
        t--;
    }
    return 0;
}