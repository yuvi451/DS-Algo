    //Works only for directed graph
    int start = 1;
    int end = 5;
    int n = 5; //size of graph

    //adjacency list: adj[a] = {{b, w}, {b1, w1}, ...} : all edges from node a, that end at b & have weight w

    vvl adj[n + 1];
    adj[1].pb({3, 3});
    adj[1].pb({2, 5});
    adj[1].pb({4, 7});
    adj[2].pb({4, 3});
    adj[2].pb({5, 2});
    adj[3].pb({4, 1});
    adj[4].pb({5, 2});

    //ditance[x] = minimum distance of node x from starting node

    vl distance(n + 1, inf);
    distance[start] = 0;

    //here instead of a queue we use a deque. A deque is basically a faster queue.

    vl in_deque(n + 1);
    deque <int> dq;
    dq.push_back(start);
    in_deque[start] = 1;

    while (dq.size() != 0){
        int node = dq.front();
        dq.pop_front();
        in_deque[node] = 0;
        
        fora(x, adj[node]){
            if (!in_deque[x[0]]){
                    if (!dq.empty() && distance[x[0]] < distance[dq.front()]){
                        dq.push_front(x[0]);
                    } else {
                        dq.push_back(x[0]);
                    }
                    in_deque[x[0]] = 1;
                }
            distance[x[0]] = min(distance[x[0]], x[1] + distance[node]);
        }
    }
    cout<<distance[end];

    //This algorithm purely uses bfs approach. The Bellman-Ford algorithm also uses the bfs approach as it updates only those distance vector values in one go that lie at
    //a particular level/distance from the start. But in this process it examines all the edges, most of which are useless.
    //This algorithm makes a slight optimisation with regard to choosing which edges to pick. It only picks those edges that are adjacent to the starting node and 
    //ignores the rest (thus avoiding all the useless edges & sticking tightly to the bfs approach) 
