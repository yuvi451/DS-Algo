void dfs(vl& visited, int start, vl& ans, vl adj[]){
    fora(x, adj[start]){
        if (!(visited[x])){
            visited[x] = 1;
            ans.pb(x);
            dfs(visited, x, ans, adj);
        }
    }
}


    int start = starting_node;
    int size = number_of_nodes;
    vl adj[size + 1]; //adjacency list
    vl visited(size + 1);
    vl ans;
    visited[start] = 1;
    ans.pb(start);
    dfs(visited, start, ans, adj);


  //Time Complexity = O(n + m) : every node and edge is visited only once
  //ans vector contains the dfs ordering
  //DFS takes an adjacent/neighbouring node, visits it and then goes into the depth of that node only instead of visiting the other neighbouring nodes
  //When is reaches the end of a node, it backtracks, moves to the next neighbour and goes into its depth

