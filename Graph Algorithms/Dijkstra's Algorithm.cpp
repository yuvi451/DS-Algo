//Does not work with graph containing negative weights/negative cycles
    int n = number_of_nodes;

  //adj[a] = {{b, w}, .....} : all edges starting at node a and ending at node b with weight w

    vector<pr> adj[n + 1];
    int start = starting_node;

  //distance[x] = minimum distance of node x from starting node

    vl distance(n + 1, inf);
    distance[start] = 0;

    vl processed(n + 1);

  //priority queue contains nodes ordered by distance (with maximum element at top & minimum at bottom)

    priority_queue <pr> pq;
    pq.push({0, start});

    while (pq.size() != 0){
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


    //It assumes that once the shortest path to a vertex is found, it cannot be shortened further. It uses a priority queue to always pick the vertex 
    //with the smallest known distance that hasn't been processed yet. This ensures that once a vertex is processed, its shortest path is determined.

    //Time Complexity = O(n + mlog(m))
    //The priority queue contains negative distances to nodes. The reason for this is that the default version of the C++ priority queue finds maximum elements, 
    //while we want to find minimum elements. By using negative distances, we can directly use the default priority queue.
