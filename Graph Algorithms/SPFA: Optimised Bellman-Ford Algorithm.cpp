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
    vl visited(n + 1);
    queue <int> q;
    q.push(start);
    visited[start] = 1;
    while (q.size() != 0){
        int node = q.front();
        q.pop();
        fora(x, adj[node]){
            if (!(visited[x[0]])){
                visited[x[0]] = 1;
                q.push(x[0]);
            }
            distance[x[0]] = min(distance[x[0]], x[1] + distance[node]);
        }
    }
    cout<<distance[end];

    //This algorithm purely uses bfs approach. The Bellman-Ford algorithm also uses the bfs approach as it updates only those distance vector values in one go that lie at
    //a particular level/distance from the start. But in this process it examines all the edges, most of which are useless.
    //This algorithm makes a slight optimisation with regard to choosing which edges to pick. It only picks those edges that are adjacent to the starting node and 
    //ignores the rest (thus avoiding all the useless edges & sticking tightly to the bfs approach) 
