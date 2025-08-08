int PrimsAlgorithm(ll n, vvl edges, vvl& ans){
        /* 
        all nodes that have been visited are connected by some sort of MST among them
        at this instant the priority queue holds all the outgoing edges from all the nodes
        and we pick up the smallest outgoing edge that expands our MST
        */
    
    vector<vector<pair<int, int>>>adj(n + 1);
    for(auto it: edges){
        int u = it[0], v = it[1], wt = it[2];
        adj[u].push_back({v, wt});
        adj[v].push_back({u, wt});
    }
    
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>>pq;
    pq.push({0, 0});
    int ans = 0;
    vector<int>visited(n + 1);
    
    while (!pq.empty()){
        int wt = pq.top().first;
        int node = pq.top().second;
        pq.pop();
        
        if (visited[node]) continue;
        ans += wt;
        visited[node] = 1;
        
        for(auto it: adj[node]){
            pq.push({it.second, it.first});
        }
    }
    return ans;
}

//inputs
ll n;
vvl ans;
vvl edges;

// intuition of this algorithm : Greedy 
// Time complexity = O(n + m*log(m))
//here forming the adjacency list also takes up some time. If it is already given then that time is saved
