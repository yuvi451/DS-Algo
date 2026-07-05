// DFS based approach
void dfs(vector<vector<int>>&adj, int root, stack<int>&st, vector<int>&visited){
      visited[root] = 1;

      for(auto it: adj[root]){
          if (!visited[it]){
              dfs(adj, it, st, visited);
          }
      }
      
      st.push(root);
  }
  vector<int> topoSort(int V, vector<vector<int>>& edges) {
      vector<vector<int>>adj(V);
      for(auto it: edges){
          int u = it[0], v = it[1];
          adj[u].push_back(v);
      }
      vector<int>ans, visited(V);
      stack<int>st;
      for(int i = 0; i < V; i++){
          if (!visited[i]) dfs(adj, i, st, visited);
      }
      while (!st.empty()){
          ans.push_back(st.top());
          st.pop();
      }
      return ans;
  }

// BFS based approach: Kahn's Algorithm
vector<int> topoSort(int V, vector<vector<int>>& edges) {
      vector<vector<int>>adj(V);
      vector<int>indegree(V), ans;
      
      for(auto it: edges){
          int u = it[0], v = it[1];
          adj[u].push_back(v);
          indegree[v]++;
      }
      
      queue<int>q;
      for(int i = 0; i < V; i++){
          if (!indegree[i]) {
              q.push(i);
              ans.push_back(i);
          }
      }
      
      while (!q.empty()){
          int node = q.front();
          q.pop();
          
          for(auto it: adj[node]){
              indegree[it]--;
              if (!indegree[it]){
                  q.push(it);
                  ans.push_back(it);
              }
          }
      }
      return ans;
  }
