bool bipartite(vector<vector<int>>& graph, int root, vector<int>& color, vector<int>& visited){
      visited[root] = 1;

      for(auto it: graph[root]){
          if (!visited[it]){
              color[it] = (color[root] + 1) % 2;
              if (!bipartite(graph, it, color, visited)) return false;
          } else if (color[it] == color[root]) return false;
      }
      return true;
  }
  bool isBipartite(vector<vector<int>>& graph) {
      int n = graph.size();
      vector<int>color(n), visited(n);
      for(int i = 0; i < n; i++){
          if (!visited[i] && !bipartite(graph, i, color, visited)) return false;
      }
      return true;
  }
