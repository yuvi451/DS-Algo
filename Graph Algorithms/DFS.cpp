void solve(vector<vector<int>>& adj, int root, vector<int>&visited, vector<int>&ans){
    visited[root] = 1;
    ans.push_back(root);
    
    for(auto it: adj[root]){
        if (!visited[it]){
            solve(adj, it, visited, ans);
        }
    }
}

vector<int> dfs(vector<vector<int>>& adj) {
    int n = adj.size();
    vector<int>ans, visited(n);
    int root = 0;
    solve(adj, root, visited, ans);
    return ans;
}

  //Time Complexity = O(n + m) : every node and edge is visited only once
  //ans vector contains the dfs ordering
  //DFS takes an adjacent/neighbouring node, visits it and then goes into the depth of that node only instead of visiting the other neighbouring nodes
  //When it reaches the end of a node, it backtracks, moves to the next neighbour and goes into its depth

