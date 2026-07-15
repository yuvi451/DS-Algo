/* 
        all nodes that have been visited are connected by some sort of MST among them (P nodes connected by P-1 edges)
        at this instant the priority queue holds all the outgoing edges from all these visited nodes
        and we pick up the smallest outgoing edge that expands our MST i.e we add a new node through an edge and
        add all the outgoing edges of the new node as well
        
        make sure to add only those edges that have not yet been visited
*/

// when only MST sum is to be returned
int spanningTree(int V, vector<vector<int>>& edges) {
        vector<vector<pair<int, int>>>adj(V);
        for(auto it: edges){
            int u = it[0], v = it[1], w = it[2];
            adj[u].push_back({v, w});
            adj[v].push_back({u, w});
        }
        priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>>pq;
        pq.push({0, 0});
        vector<int>visited(V);
        int sum = 0;

        // E times
        while (!pq.empty()){
            int wt = pq.top().first, node = pq.top().second;        // logE
            pq.pop();
            
            if (visited[node]) continue;
            visited[node] = 1;
            sum += wt;
            
            for(auto it: adj[node]){
                    // logE
                if (!visited[it.first]) pq.push({it.second, it.first});  // be very careful about this !visited[it] thing, it saves memory
            }
        }
        return sum;
}

// when entire MST is to be returned
vector<pair<int, int>> spanningTree(int V, vector<vector<int>>& edges) {
        vector<vector<pair<int, int>>>adj(V);
        for(auto it: edges){
            int u = it[0], v = it[1], w = it[2];
            adj[u].push_back({v, w});
            adj[v].push_back({u, w});
        }
        priority_queue<vector<int>, vector<vector<int>>, greater<vector<int>>>pq;
        pq.push({0, 0, -1});
        vector<int>visited(V);
        int sum = 0;
        vector<pair<int, int>>v;

        // E times
        while (!pq.empty()){
            int node = pq.top()[1], par = pq.top()[2], wt = pq.top()[0];        // logE
            pq.pop();
            
            if (visited[node]) continue;
            visited[node] = 1;
            sum += wt;
            
            if (par != -1) v.push_back({node, par});
            
            for(auto it: adj[node]){
                    // logE
                if (!visited[it.first]){        // be very careful about this !visited[it] thing, it saves memory
                    pq.push({it.second, it.first, node});
                }
            }
        }
        return v;
    }

// intuition of this algorithm : Greedy 
// Time complexity = O(E*logE)
