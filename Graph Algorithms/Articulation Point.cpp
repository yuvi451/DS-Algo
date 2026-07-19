void dfs(vector<vector<int>>&adj, vector<int>&low, vector<int>&disc, int& time, int u, int par, vector<int>&mark){
      time++;
      disc[u] = low[u] = time;
      int children = 0; // disconnected children
      
      for(auto it: adj[u]){
          if (disc[it] == -1){
              children++;
              dfs(adj, low, disc, time, it, u, mark);
              low[u] = min(low[u], low[it]);
              
              if (par != -1 && low[it] >= disc[u]) mark[u] = 1;
          } else if (it != par) low[u] = min(low[u], disc[it]);
      }
      
      if (par == -1 && children > 1) mark[u] = 1;
   }

  vector<int> articulationPoints(int V, vector<vector<int>>& edges) {
      vector<vector<int>>adj(V);
      for(auto it: edges){
          int u = it[0], v = it[1];
          adj[u].push_back(v);
          adj[v].push_back(u);
      }
      int time = 0;
      vector<int>low(V), disc(V, -1), ans, mark(V);
      for(int i = 0; i < V; i++){
          if (disc[i] == -1) dfs(adj, low, disc, time, i, -1, mark);
      }
      
      for(int i = 0; i < V; i++) if (mark[i]) ans.push_back(i);
      
      if (ans.size()) return ans;
      else return {-1};
  }
