void Dijkstra(vvl edges, int nodes, int root, vl& distance){
    distance[root] = 0;
    vector <vpr> adj(nodes + 1);
    fora(x, edges){
        adj[x[0]].pb({x[1], x[2]});
    }

    vl processed(nodes + 1);

    priority_queue <pr> pq;
    pq.push({0, root});

    while (!pq.empty(){
        int node = pq.top().second;
        pq.pop();

        if (processed[node]) continue;
        processed[node] = 1;

        fora(x, adj[node]){
            if (distance[x.first] > distance[node] + x.second){
                distance[x.first] = distance[node] + x.second;
                pq.push({-distance[x.first], x.first});
            }
        }
    }
}
    
     //Does not work with graphs containing negative weights/negative cycles [gets stuck in infinite loop]
     //priority queue contains nodes ordered by distance (with maximum element at top)
    //It assumes that once the shortest path to a vertex is found, it cannot be shortened further. 
    //It uses a priority queue to always pick the vertex with the smallest known distance that hasn't been processed yet. 
    //This ensures that once a vertex is processed, its shortest path is determined.

    //Time Complexity = O(n + m*log(m))
    //The priority queue contains negative distances to nodes. The reason for this is that the default version of the C++ priority queue finds maximum elements, 
    //while we want to find minimum elements. By using negative distances, we can directly use the default priority queue.
