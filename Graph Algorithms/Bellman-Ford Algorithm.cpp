void BellmanFord(vvl edges, vl& distance, int nodes, int start, int& r){
    distance[start] = 0;
    forl(i, 0, nodes - 1){
        fora(x, edges){
            if (distance[x[1]] > distance[x[0]] + x[2]){
                distance[x[1]] = distance[x[0]] + x[2];
            }
        }
    }

    //Check for negative cycles

    fora(x, edges){
        if (distance[x[1]] > distance[x[0]] + x[2]){
            r++;
        }
        break;
    }
}

    //value of r tells us about negative cycles

    //inputs
    vl distance(nodes + 1, inf);  
    int r = 0;

    //edge adjacency form where each edge is represented as {a, b, w} : starting node, ending node, weight/length of edge
    //distance[x] = shortest distance of node x from starting node

    // if number of nodes = n (size) : We do exactly n - 1 iterations
    //Why n - 1 ? because this algorithm is based on bfs approach i.e. it first updates only those nodes distances which are adjacent to the starting node, then in the 
    //next iteration it works for neighbours of these nodes and so on. Now this bfs approach would require n - 1 iterations in the worst case so as to explore all the levels.

    //if it contains negative cycles then only it will update in n-th round

    //Time complexity = O(n*m)
