class SCC {
    private: 
        vector<vector<int>>adj, ans, adjRev;
        int V;
        vector<int>visited1, visited2;
        stack<int>st;

        void dfs1(int i){
            visited1[i] = 1;

            for(auto it: adj[i]){
                if (!visited1[it]) dfs1(it);
            }
            st.push(i);
        }

        void dfs2(int i, vector<int>& temp){
            visited2[i] = 1;

            for(auto it: adjRev[i]){
                if (!visited2[it]) dfs2(it, temp);
            }
            temp.push_back(i);
        }

    public:
        SCC(vector<vector<int>> adjList){
            adj = adjList;
            V = adj.size();
            visited1.resize(V);
            visited2.resize(V);
            adjRev.resize(V);
            
            for(int i = 0; i < V; i++){
                for(auto it: adj[i]){
                    int u = i, v = it;
                    adjRev[v].push_back(u);
                }
            }
        }

        vector<vector<int>> solve(){
            for(int i = 0; i < V; i++){
                if (!visited1[i]){
                    dfs1(i);
                }
            }

            while (!st.empty()){
                int t = st.top();
                st.pop();
                if (!visited2[t]){
                    vector<int>temp;
                    dfs2(t, temp);
                    ans.push_back(temp);
                }
            }
            
            return ans;
        }
};
