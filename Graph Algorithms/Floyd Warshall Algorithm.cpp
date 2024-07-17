
void FloydWarshall(vvl edges, vvl& distance, int nodes){
    fora(x, edges){
        distance[x[0]][x[1]] = x[2];
    }

    forl(i, 0, nodes + 1){
        distance[i][i] = 0; 
    }

    //nodes are 1 base indexed

    forl(k, 1, nodes + 1){
        forl(i, 1, nodes + 1){
            forl(j, 1, nodes + 1){
                if (distance[i][k] < inf && distance[k][j] < inf){
                    distance[i][j] = min(distance[i][j], distance[i][k] + distance[k][j]);
                }
            }
        }
    }
}

    //inputs
    vvl distance(nodes + 1, vl(nodes + 1, inf));

    //Can detect negative cycles if distance[i][i] < 0 

    //adjacency list to adjacency matrix conversion. 
    forl(i, 1, n + 1){
        distance[i][i] = 0;
        fora(x, adj[i]){
            distance[i][x[0]] = x[1];
        }
    }

    //If adjacency matrix is given directly copy it and replace all zeroes with infinity

    //Time complexity = O(n^3)
    //Best suited for dense graphs and when you need shortest paths between all pairs of vertices. It works for graphs with both positive 
    //and negative edge weights but without negative weight cycles.
