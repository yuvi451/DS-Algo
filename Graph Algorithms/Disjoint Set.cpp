// Finds whether two elements belong to the same component or not in O(4*alpha) == O(1) time
// if (ds.findUtlPar(i) == ds.findUltPar(j)) then i & j belong to the same component
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


