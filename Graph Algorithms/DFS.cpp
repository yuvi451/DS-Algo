void DFS(vvl& adj, vl& visited, int start, vl& ans){
    if (!(visited[start])){
        visited[start] = 1;
        ans.pb(start);
    }

    fora(x, adj[start]){
        if (!(visited[x])){
            visited[x] = 1;
            ans.pb(x);
            DFS(adj, visited, x, ans);
        }
    }
}

  //Time Complexity = O(n + m) : every node and edge is visited only once
  //ans vector contains the dfs ordering
  //DFS takes an adjacent/neighbouring node, visits it and then goes into the depth of that node only instead of visiting the other neighbouring nodes
  //When it reaches the end of a node, it backtracks, moves to the next neighbour and goes into its depth

