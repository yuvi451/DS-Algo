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

void BUILD_SUM(vector<int> &arr, vector<int> &t, int v, int tl, int tr){
    if (tl == tr) {
        t[v] = arr[tl];
    } else {
        int tm = (tl + tr)/2;
        BUILD_SUM(arr, t, 2*v, tl, tm);
        BUILD_SUM(arr, t, 2*v + 1, tm + 1, tr);
        t[v] = t[2*v] + t[2*v + 1];
    }
}

int SUM(int l, int r, vector<int> &t, int v, int tl, int tr){
    if (l > r) return 0;

    if (tl == l && tr == r) return t[v];

    int tm = (tl + tr)/2;
    return SUM(l, min(tm, r), t, 2*v, tl, tm) + SUM(max(tm + 1, l), r, t, 2*v + 1, tm + 1, tr);
}

void UPDATE(int pos, int value, vector<int> &t, int v, int tl, int tr){
    if (tl == tr) {
        if (pos == tl) t[v] = value;
    } else {
        int tm = (tl + tr)/2;
        if (pos <= tm){
            UPDATE(pos, value, t, 2*v, tl, tm);
        } else {
            UPDATE(pos, value, t, 2*v + 1, tm + 1, tr);
        }
        t[v] = t[2*v] + t[2*v + 1];
    }
}

void BUILD_MAXIMUM(vector<int> &arr, vector<int> &t, int v, int tl, int tr){
    if (tl == tr) {
        t[v] = arr[tl];
    } else {
        int tm = (tl + tr)/2;
        BUILD_MAXIMUM(arr, t, 2*v, tl, tm);
        BUILD_MAXIMUM(arr, t, 2*v + 1, tm + 1, tr);
        t[v] = max(t[2*v], t[2*v + 1]);
    }
}

int MAXIMUM(int l, int r, vector<int> &t, int v, int tl, int tr){
    if (l > r) return 0;

    if (tl == l && tr == r) return t[v];

    int tm = (tl + tr)/2;
    return max(MAXIMUM(l, min(tm, r), t, 2*v, tl, tm), MAXIMUM(max(tm + 1, l), r, t, 2*v + 1, tm + 1, tr));
}

int main(){
    ios::sync_with_stdio(0);
    cin.tie(0);
    vector<int>arr = {2, -5, 6, 8, 12, -7, 5, 3};
    int n = arr.size();
    vector<int>t(4*n);
    BUILD_MAXIMUM(arr, t, 1, 0, n - 1);
    cout<<MAXIMUM(5, 5, t, 1, 0, n - 1);
    return 0;
}
