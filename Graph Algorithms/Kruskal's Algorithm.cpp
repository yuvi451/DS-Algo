class DisjointSet {
    private: 
        vector<int>rank, size, parent;

    public:
        DisjointSet(int n){
            rank.resize(n + 1);
            size.resize(n + 1);
            parent.resize(n + 1);

            for(int i = 0; i <= n; i++) {
                parent[i] = i;
                size[i] = 1;
            }
        }

        int findPar(int x){
            if (parent[x] == x) return x;
            return parent[x] = findPar(parent[x]);
        }

        void unionByRank(int x, int y){
            int ut_x = findPar(x);
            int ut_y = findPar(y);
            if (ut_x == ut_y) return;

            if (rank[ut_x] < rank[ut_y]){
                parent[ut_x] = ut_y;
            } else if (rank[ut_x] > rank[ut_y]){
                parent[ut_y] = ut_x;
            } else {
                parent[ut_x] = ut_y;
                rank[ut_y]++;
            }
        }

        void unionBySize(int x, int y){
            int ut_x = findPar(x);
            int ut_y = findPar(y);
            if (ut_x == ut_y) return;

            if (size[ut_x] < size[ut_y]){
                parent[ut_x] = ut_y;
                size[ut_y] += size[ut_x];
            } else {
                parent[ut_y] = ut_x;
                size[ut_x] += size[ut_y];
            }
        }
};

class Solution {
  public:
    int spanningTree(int V, vector<vector<int>> adj[]) {
        vector<vector<int>>edges;
        for(int i = 0; i < V; i++){
            for(auto it: adj[i]){
                int u = i, v = it[0], wt = it[1];
                edges.push_back({u, v, wt});
            }
        }
        sort(edges.begin(), edges.end(), [](vector<int>&a, vector<int>&b) {
            return a[2] < b[2];
        });
        int ans = 0;
        DisjointSet ds(V);
        for(auto it: edges){
            if (ds.findPar(it[0]) != ds.findPar(it[1])){
                ans += it[2];
            }
            ds.unionByRank(it[0], it[1]);
            
        }
        return ans;
    }
};
