vector<vector<int>> floydWarshall(vector<vector<int>>& edges, int n){
    // nodes 0 - n-1
    vector<vector<int>>distance(n, vector<int>(n, 1e8));
    for(auto it: edges){
        int u = it[0], v = it[1], w = it[2];
        distance[u][v] = w;
        // if undirected graph
        distance[v][u] = w;
    }

    for(int i = 0; i < n; i++) distance[i][i] = 0;

    for(int k = 0; k < n; k++){
        for(int i = 0; i < n; i++){
            for(int j = 0; j < n; j++){
                if (distance[i][k] != 1e8 && distance[k][j] != 1e8){
                    distance[i][j] = min(distance[i][j], distance[i][k] + distance[k][j]);
                }
            }
        }
    }

    return distance;
}

//Can detect negative cycles if distance[i][i] < 0 

for (int i = 0; i < n; i++) {
    if (distance[i][i] < 0) {
        // A negative-weight cycle exists.
    }
}

//Time complexity = O(n^3)
//Best suited for dense graphs and when you need shortest paths between all pairs of vertices. It works for graphs with both positive 
//and negative edge weights but without negative weight cycles.
