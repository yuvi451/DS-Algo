// DFS based approach
bool dfs(vector<vector<int>>&adj, int root, vector<int>& visited, vector<int>& path){
      visited[root] = 1;
      path[root] = 1;
      
      for(auto it: adj[root]){
          if (!visited[it]){
              if (dfs(adj, it, visited, path)) return true;
          } else if (path[it] == 1) return true;
      }
      
      path[root] = 0;
      return false;
  }
  bool isCyclic(int V, vector<vector<int>> &edges) {
      vector<vector<int>>adj(V);
      for(auto it: edges){
          int u = it[0], v = it[1];
          adj[u].push_back(v);
      }
      vector<int>visited(V), path(V);
      for(int i = 0; i < V; i++){
          if (!visited[i] && dfs(adj, i, visited, path)) return true;
      }
      return false;
  }
