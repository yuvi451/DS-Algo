void dfs(vvl adj, vl& distance, int root, int prev_root = 0){
    if (adj[root].size() == 1 && adj[root][0] == prev_root){
        distance[root] = 1 + distance[prev_root];
    }
    fora(x, adj[root]){
        if (x != prev_root){
            distance[x] = 1 + distance[root];
            dfs(adj, distance, x, root);
        }
    }
}

//The above function finds distance of each node from root
//inputs for above code
  vl distance(adj.size() + 1);

ll diamter(vvl adj){
    int n = adj.size();
    vl distance(n + 1);
    int starting_node = 1;
  
    dfs(adj, distance, starting_node);
  
    int r = 0, s = 0;
    forl(i, 0, n + 1){
        if (distance[i] > s){
            s = distance[i];
            r = i;
        }
    }
  
    vl dist(n + 1);
  
    dfs(adj, dist, r);
  
    ll ans = 0;
    fora(x, dist){
        ans = max(ans, x);
    }
    return ans;
}

  //Finds the diameter of tree in O(n) time
