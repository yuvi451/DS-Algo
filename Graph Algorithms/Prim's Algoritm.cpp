struct Compare {
    bool operator()(const vl& a, const vl& b) {
        return a[0] > b[0]; 
    }
};

void PrimsAlgorithm(ll n, vvl edges, vvl& ans){
    vl visited(n + 1);
    ll mst = 0;
    vector <vector<pr>>adj(n + 1);
  
    fora(x, edges){
        adj[x[0]].pb({x[1], x[2]});
        adj[x[1]].pb({x[0], x[2]});
    }
  
    priority_queue <vl, vvl, Compare> pq;
    pq.push({0, 0, -1});
    // {weight, node, parent}
  
    while (!(pq.empty())){
        vl v = pq.top();
        pq.pop();
        if (visited[v[1]]) continue;
        visited[v[1]] = 1;
        mst += v[0];
        if (v[2] != -1){
            ans.pb({v[2], v[1]});
        }
        fora(x, adj[v[1]]){
            if (!(visited[x.first])){
                pq.push({x.second, x.first, v[1]});
            }
        }
    }
    cout<<mst;
}

//inputs
ll n;
vvl ans;
vvl edges;

// intuition of this algorithm : Greedy 
// Time complexity = O(n + m*log(m))
//here forming the adjacency list also takes up some time. If it is already given then that time is saved
