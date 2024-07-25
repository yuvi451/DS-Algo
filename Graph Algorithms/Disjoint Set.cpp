class DisjointSet{
    vl rank, parent, size;
    public:
    DisjointSet(int n){
        rank.resize(n + 1, 0);
        parent.resize(n + 1);
        size.resize(n + 1, 1);
        forl(i, 0, n + 1){
            parent[i] = i;
        }
    }

    int findUltPar(int node){
        if (node == parent[node]) return node;
        else return parent[node] = findUltPar(parent[node]);
    }

    void UnionByRank(int u, int v){
        int ult_u = findUltPar(u);
        int ult_v = findUltPar(v);
        if (ult_u == ult_v) return;
        else if (rank[ult_u] > rank[ult_v]){
            parent[ult_v] = ult_u;
        } else if (rank[ult_u] < rank[ult_v]){
            parent[ult_u] = ult_v;
        } else {
            parent[ult_u] = ult_v;
            rank[ult_v]++;
        }
    }

    void UnionBySize(int u, int v){
            int ult_u = findUltPar(u);
            int ult_v = findUltPar(v);
            if (ult_u == ult_v) return;
            else if (size[ult_u] > size[ult_v]){
                parent[ult_v] = ult_u;
                size[ult_u] += size[ult_v];
            } else if (size[ult_u] < size[ult_v]){
                parent[ult_u] = ult_v;
                size[ult_v] += size[ult_u];
            } else {
                parent[ult_u] = ult_v;
                size[ult_v] += size[ult_u];
            }
        }
};

