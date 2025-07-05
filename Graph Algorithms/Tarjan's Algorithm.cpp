class SCC {
    private: 
        vector<vector<int>>adj, ans;
        int V, time;
        stack<int>st;
        vector<int>disc, low, instack;

        void dfs(int i){
            time++;
            disc[i] = time, low[i] = time;
            st.push(i);
            instack[i] = 1;

            for(auto it: adj[i]){
                if (disc[it] == -1){
                    dfs(it);
                    low[i] = min(low[i], low[it]);
                } else if (instack[it]){
                    low[i] = min(low[i], disc[it]);
                }
            }

            if (disc[i] == low[i]){
                vector<int>temp;
                while (st.top() != i){
                    temp.push_back(st.top());
                    instack[st.top()] = 0;
                    st.pop();
                }
                temp.push_back(st.top());
                instack[st.top()] = 0;
                st.pop();
        
                ans.push_back(temp);
            }
        }

    public:
        SCC(vector<vector<int>> adjList){
            adj = adjList;
            V = adj.size();
            time = 0;
            disc.resize(V, -1);
            low.resize(V, -1);
            instack.resize(V);
        }

        vector<vector<int>> solve(){
            for(int i = 0; i < V; i++){
                if (disc[i] == -1){
                    dfs(i);
                }
            }
            return ans;
        }
};
