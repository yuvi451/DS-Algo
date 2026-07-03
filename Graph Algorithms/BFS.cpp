vector<int> bfs(vector<vector<int>> &adj) {
    int n = adj.size();
    vector<int>ans, visited(n + 1);
    queue<int>q;
    int root = 0;
    visited[root] = 1;
    q.push(root);
    
    while (!q.empty()){
        int node = q.front();
        q.pop();
        ans.push_back(node);
        
        for(auto it: adj[node]){
            if (!visited[it]){
                visited[it] = 1;
                q.push(it);
            }
        }
    }
    return ans;
}

// Time Complexity = O(n + m) : every node and edge is visited only once
// ans vector stores BFS ordering
// BFS is a level by level traversal algorithm i.e. first all nodes that are at level 0 (distance 0 from root i.e. root itself) are processed, then all the nodes at level 1 (distance 1 from root), then level 2 and so on are processed
// All nodes of a level are processed from left to right
// Intuititon: intially the queue stores all the nodes of level 0 (root only) then once root is popped level 0 is completely processed; After that we push entire level 1 into the queue (root's children)
// Because of first in first out property of queue first all the nodes of level 1 get processed then only nodes of level 2 begin getting processed
// As we pop out nodes of level 1 we push their children i.e. nodes of level 2 into the queue (these obv. get processed after level 1)
// When entire level 1 is popped out the queue is full of level 2 nodes
// Finally all the level 2 nodes get processed first before any level 3 nodes processing can begin...

  
