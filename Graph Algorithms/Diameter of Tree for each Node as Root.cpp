// in[x] = maximum depth/distance that can be reached in the subtree of node x
void dfs1(vvl adj, vl& in, int root, int prev_root = -1){
    fora(x, adj[root]){
        if (x != prev_root){
            /* 
            in[x] = 1 + in[root]; this is not the maximum depth in the subtree of node x but 
            is actually the distance of node from the root of the entire tree
            */
            dfs1(adj, in, x, root);
            /*
            while backtracking we iterate over all siblings of node x and pick up the one that gives us the maximum depth
           */
            in[root] = max(in[root], 1 + in[x]);
        }
    }
}

/*
now we want to find the maximum depth that we can traverse by rooting each node once in O(N) time

well if root the tree arbitrarily the maximum depth/distance that can covered (starting from this node) would lie either inside or outside the subtree
here in[x] denotes the maximum depth that can be covered inside the subtree 

Now to find out[x]
Our logic is: We would definitely go the parent of the current node. From parent node there are two paths: either we go outside the subtree 
of the parent or we stay in the subtree and explore a different sibling which would make out[x] = 1 + max(1 + in[sibiling], out[parent])

Instead of approaching this problem iteratively/ recursively we use a different logic. We go the parent of node x and then iterate over all 
its children (which would include node x as well). Then we find two maximum (largest && second largest; mx1 && mx2) distances can be traversed in the subtrees of its children 

As we approach this problem from bottom to top we basically have out[original root] = 0 {no subtree}. Then while iterating over its children we 
use this result as out[parent] and are only left with the problem of calculating the maximum possible distance across its siblings. 
If the mx1 = in[x] (mx1 already taken) then we take mx2 to be the candidate for maximum sibling distance, otherwise we use mx1 coz its the maximum outside sibling distance
use = mx1 or mx2 whichever we would be using

Now maximum sibling distance outside the subtree of the current node is 2 + use

2 + max(in[sibling]) = 2 + use

out[x] = longest path that can be covered outside the subtree of node x
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
            if (in[x] == mx1){
                use = mx2;
            }
            out[x] = max(1 + out[root], 2 + use);
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
