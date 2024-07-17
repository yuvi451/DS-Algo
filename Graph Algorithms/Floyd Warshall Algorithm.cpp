  //Can detect negative cycles if adj_matrix[i][i] < 0 

    int n = 5; // number of nodes / size of graph

    vector<pr> adj[n + 1];
    adj[1] = {{5, 1}, {2, 5}, {4, 9}};
    adj[2] = {{1, 5}, {3, 2}};
    adj[3] = {{2, 2}, {4, 7}};
    adj[4] = {{3, 7}, {5, 2}, {1, 9}};
    adj[5] = {{4, 2}, {1, 1}};

    vvl adj_matrix(n + 1, vl(n + 1, inf));

    //adjacency list to adjacency matrix conversion. If adjacency matrix is given directly copy it and replace all zeroes with infinity

    forl(i, 1, n + 1){
        adj_matrix[i][i] = 0;
        fora(x, adj[i]){
            adj_matrix[i][x.first] = x.second;
        }
    }

    //Actual algorithm

    forl(k, 1, n + 1){
        forl(i, 1, n + 1){
            forl(j, 1, n + 1){
                adj_matrix[i][j] = min(adj_matrix[i][j], adj_matrix[i][k] + adj_matrix[k][j]);
            }
        }
    }

    //Time complexity = O(n^3)
    //Best suited for dense graphs and when you need shortest paths between all pairs of vertices. It works for graphs with both positive 
    //and negative edge weights but without negative weight cycles.
