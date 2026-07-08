vector<int> bellmanFord(int V, vector<vector<int>>& edges, int src) {
    vector<int>distance(V, 1e8);
    distance[src] = 0;
    for(int i = 0; i < V - 1; i++){
        for(auto& it: edges){
            int u = it[0], v = it[1], w = it[2];
            if (distance[u] != 1e8 && distance[v] > distance[u] + w){
                distance[v] = distance[u] + w;
            }
        }
    }
    
    for(auto& it: edges){
        int u = it[0], v = it[1], w = it[2];
        if (distance[u] != 1e8 && distance[v] > distance[u] + w) return {-1};
    }
    
    return distance;
}    
    // we put check distance[u] != 1e8 coz if w becomes -ve then distance[v] gets updated to 1e8 - abs(w)
    
    // At its core, Bellman-Ford isn't just a graph traversal algorithm; it is a Dynamic Programming state machine. In this algorithm iteration can be seen as
    // incrementally expanding the maximum number of edges allowed in our paths.
    // it begins with this dp formulation: Let dp[k][v] represent the shortest path distance from the source node S to node v using at most k edges. and then some more jargon and finally 
    // simplifies to distance[v] = distance[u] + w;
    //distance[x] = shortest distance of node x from starting node

    // if number of nodes = n (size) : We do exactly n - 1 iterations
    //Why n - 1 ? because this algorithm is based on bfs approach i.e. it first updates only those nodes distances which are adjacent to the starting node, then in the 
    //next iteration it works for neighbours of these nodes and so on. Now this bfs approach would require n - 1 iterations in the worst case so as to explore all the levels.

    // In any graph with |V| vertices, the absolute longest possible simple path (a path with no repeated vertices) can contain at most |V| - 1 edges.

    //if it contains negative cycles then only it will update in n-th round

    //Time complexity = O(n*m)
