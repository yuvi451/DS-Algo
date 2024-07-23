// in[x] =  longest path from each node to any of its descendants (inside its subtree)

void dfs1(vvl adj, vl& in, int root, int prev_root = -1){
    fora(x, adj[root]){
        if (x != prev_root){
            dfs1(adj, in, x, root);
            /*
             while backtracking we explore all the siblings of a node and find which 
            sibling leads to maximum distance 
           */
            in[root] = max(in[root], 1 + in[x]);
        }
    }
}

/*
out[x] = the longest path from each node to any node outside its subtree
out[x] = max(1 + out[root/parent], 2 + in[v]) where v is a sibling of x
We have in[v] calculated from above
And we also have out[root] from previous steps
Now we just need to explore the possibility where maximum distance can go through siblings of node x
*/
 

void dfs2(vvl adj, vl in, vl& out, int root, int prev_root = 0){
    int mx1 = -1, mx2 = -1;
    fora(x, adj[root]){
        if (x != prev_root){
            if (in[x] >= mx1) mx2 = mx1, mx1 = in[x];
            else if (in[x] > mx2) mx2 = in[x];
        }
    }
    fora(x, adj[root]){
        if (x != prev_root){
            ll use = mx1;
            /* 
            out[root taken in begining] = 0 [No subtree] Here out[1] = 0;

            To calculate out[node] 

            We firstly take root of the node and then for this root we explore all its 
            children and store the two maximum distances that can be traversed in their subtrees

            Basically we know that 
            out[node] = max(1 + out[root], 2 + use)
            either we go outside the subtree of root or we go along the longest sibling

            use = mx1 by default but if in[node] = mx1 (then this path is already taken) 
            we use the second maximum value use = mx2; and + 2 for the fact that we go 
            to parent first then to the sibling and finally mx2 

            */
            if (in[x] == mx1){
                use = mx2;
            }
            out[x] = max(1 + out[root], 2 + use);
            /* This a bottom-up approach i.e. we calculate lower values first to calculate higher values
            
               The logic is simple if we out[root] for a particular root then we can use it to calculate out[child] for 
               each of its children
            */
            dfs2(adj, in, out, x, root);
        }
    }
}

// inputs
    vl in(n + 1);
    vl out(n + 1);
    dfs1(adj, in, 1);
    dfs2(adj, in, out, 1);
    forl(i, 1, n + 1){
        cout<<i<<" "<<max(in[i], out[i])<<"\n";
    }

// Time complexity = O(N)
