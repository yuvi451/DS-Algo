void BFS(vvl adj, vl& ans, int root){
    int n = adj.size();
    vl visited(n + 1), distance(n + 1);

    queue <int> q;
    q.push(root);
    visited[root] = 1;
    ans.pb(root);

    while (!q.empty(){
        int node = q.front();
        q.pop();

        fora(x, adj[node]){
            if (!(visited[x])){
                visited[x] = 1;
                distance[x] = distance[node] + 1;
                q.push(x);
                ans.pb(x);
            }
        }
    }
}

  //Time Complexity = O(n + m) : every node and edge is visited only once
  //ans vector stores bfs ordering
  //BFS is a level by level search algorithm i.e. we first look for all elements that are adjacent to the starting node and then only look for elements 
  //that are at adjacent to the first neighbours of the starting node [Breadth/Horizontal First Search]
  //Unlike DFS it picks up a neighbour (adjacent element), visits it and then goes on to the next neighbour (which is also adjacent to the start)
  
