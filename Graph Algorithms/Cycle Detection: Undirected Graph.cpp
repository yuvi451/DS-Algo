// DFS based approach
bool dfs(vector<vector<int>>&adj, int root, int par, vector<int>& visited){
      visited[root] = 1;
      
      for(auto it: adj[root]){
          if (!visited[it]){
              if (dfs(adj, it, root, visited)) return true;
          } else if (it != par) return true;
      }
      return false;
  }

  bool isCycle(int V, vector<vector<int>>& edges) {
      vector<vector<int>>adj(V);
      for(auto it: edges){
          int u = it[0], v = it[1];
          adj[u].push_back(v);
          adj[v].push_back(u);
      }
      
      vector<int>visited(V);
      for(int i = 0; i < V; i++){
          if (!visited[i] && dfs(adj, i, -1, visited)) return true;
      }
      return false;
  }


// BFS based approach
bool isCycle(int V, vector<vector<int>>& edges) {
      vector<vector<int>>adj(V);
      for(auto it: edges){
          int u = it[0], v = it[1];
          adj[u].push_back(v);
          adj[v].push_back(u);
      }
      
      vector<int>visited(V);
      for(int i = 0; i < V; i++){
          if (visited[i] == 1) continue;
          
          int root = i;
          queue<pair<int, int>>q;
          visited[root] = 1;
          q.push({root, -1});
          
          while (!q.empty()){
              int node = q.front().first, par = q.front().second;
              q.pop();
              
              for(auto it: adj[node]){
                  if (!visited[it]){
                      visited[it] = 1;
                      q.push({it, node});
                  } else if (it != par) return true;
              }
          }   
      }
      return false;
  }
