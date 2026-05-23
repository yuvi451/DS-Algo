void BUILD(int v, int tl, int tr, vector<int>& sum, vector<int>& arr){
    // tl and tr are array indices
    // v is the vertex index: mode for traversing in the tree
    if (tl == tr) {
        sum[v] = arr[tl];
    } else {
        int tm = (tl + tr)/2;
        BUILD(2*v, tl, tm, sum, arr);
        BUILD(2*v + 1, tm + 1, tr, sum, arr);
        sum[v] = sum[2*v] + sum[2*v + 1];
    }
}

int SUM(int l, int r, int v, vector<int>& sum, int tl, int tr){
    // [tl, tr] is segment covered by current vertex v
    // [l, r] is the segment sum that we have to find
    if (l > r) return 0;

    if (l == tl && r == tr) return sum[v];

    int tm = (tl + tr)/2;
    // we split query [l, r] into subqueries
    // intersection between the segment of the query and the segment of the left/right child
    return SUM(l, min(r, tm), 2*v, sum, tl, tm) + SUM(max(tm + 1, l), r, 2*v + 1, sum, tm + 1, tr);

}

void UPDATE(int v, int tl, int tr, int pos, int value, vector<int>& sum){
    if (tl == tr){
        sum[v] = value;
    } else {
        int tm = (tl + tr)/2;
        if (pos <= tm){
            UPDATE(2*v, tl, tm, pos, value, sum);
        } else {
            UPDATE(2*v + 1, tm + 1, tr, pos, value, sum);
        }
        sum[v] = sum[2*v] + sum[2*v + 1];
    }
}   

int main(){
    ios::sync_with_stdio(0);
    cin.tie(0);
    vector<int>arr = {1, 4, -7, 12, 6, -3, 5, 2};
    int n = arr.size();
    vector<int>sum(4*n);
    BUILD(1, 0, n - 1, sum, arr);
    cout<<SUM(3, 7, 1, sum, 0, n - 1);
    return 0;
}
