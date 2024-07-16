    int size = number_of_nodes
    vl adj[size + 1]; // adjacency list  
    vl visited(size + 1); 
    vl ans;
    int start = starting_node;
    visited[start] = 1;
    ans.pb(start);
    queue <int> q;
    q.push(start);
    while (q.size() != 0){
        int node = q.front();
        q.pop();
        fora(x, adj[node]){
            if (!(visited[x])){
                visited[x] = 1;
                ans.pb(x);
                q.push(x);
            }
        }
    }


  //Time Complexity = O(n + m) : every node and edge is visited only once
  //ans vector stores bfs ordering; 
  //BFS is a level by level search algorithm i.e. we first look for all elements that are at distance x from starting node and then only look for elements 
  //that are at disatance x + 1 from start [Breadth/Horizontal First Search]
  //Unlike DFS it picks up a neighbour (adjacent element), visits it and then goes on to the next neighbour (which is also at same distance from start)
  
