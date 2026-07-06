vector<int> dijkstra(int V, vector<vector<int>> &edges, int src) {
    vector<vector<pair<int, int>>>adj(V);
    
    for(auto it: edges){
        int u = it[0], v = it[1], wt = it[2];
        adj[u].push_back({v, wt});
        adj[v].push_back({u, wt});
    }
    
    vector<int>distance(V, 1e9);
    distance[src] = 0;
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;
    pq.push({distance[src], src});
    
    while (!pq.empty()){
        int dist = pq.top().first;
        int node = pq.top().second;
        pq.pop();
        
        if (dist > distance[node]) continue;
        
        for(auto it: adj[node]){
            int wt = it.second;
            int nextNode = it.first;
            if (distance[nextNode] > dist + wt){
                distance[nextNode] = dist + wt;
                pq.push({distance[nextNode], nextNode});
            }
        }
    }
    
    return distance;
}
    
     //Does not work with graphs containing negative weights/negative cycles [gets stuck in infinite loop]
     //priority queue contains nodes ordered by distance (with maximum element at top)
    //It assumes that once the shortest path to a vertex is found, it cannot be shortened further. 
    //It uses a priority queue to always pick the vertex with the smallest known distance that hasn't been processed yet. 
    //This ensures that once a vertex is processed, its shortest path is determined.

    //Time Complexity = O(n + m*log(m))
    //The priority queue contains negative distances to nodes. The reason for this is that the default version of the C++ priority queue finds maximum elements, 
    //while we want to find minimum elements. By using negative distances, we can directly use the default priority queue.
