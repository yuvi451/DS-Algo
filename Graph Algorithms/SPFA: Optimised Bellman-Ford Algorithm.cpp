void SPFA(vvl edges, int nodes, vl& distance, int start, int&r){
    distance[start] = 0;
    vector <vpr> adj(nodes + 1);
    fora(x, edges){
        adj[x[0]].pb({x[1], x[2]});
    }

    deque<int>dq;
    vl in_deque(nodes + 1);
    vl update_count(nodes + 1, 0);

    dq.push_back(start);
    in_deque[start] = 1;
    

    while (dq.size() != 0){
        int node = dq.front();
        dq.pop_front();
        in_deque[node] = 0;

        fora(x, adj[node]){

            distance[x.first] = min(distance[x.first], distance[node] + x.second);
            
            if (!(in_deque[x.first])){
                if (!(dq.empty()) && distance[x.first] < distance[dq.front()]){
                    dq.push_front(x.first);
                } else {
                    dq.push_back(x.first);
                }
                in_deque[x.first] = 1;

                update_count[x.first]++;
                if (update_count[x.first] > nodes) {
                    r = 1;
                    return;
                }
            }
        }
    }
}

    //inputs
    //vl distance(nodes + 1, inf);
    //int r = 0;  for checking negative cycles (if r == 1)

    //adjacency list: adj[a] = {{b, w}, {b1, w1}, ...} : all edges from node a, that end at b & have weight w
    //here instead of a queue we use a deque. A deque is basically a faster queue.

    //This algorithm purely uses bfs approach. The Bellman-Ford algorithm also uses the bfs approach as it updates only those distance vector values in one go that lie at
    //a particular level/distance from the start. But in this process it examines all the edges, most of which are useless.
    //This algorithm makes a slight optimisation with regard to choosing which edges to pick. It only picks those edges that are adjacent to the starting node and 
    //ignores the rest (thus avoiding all the useless edges & sticking tightly to the bfs approach) 
