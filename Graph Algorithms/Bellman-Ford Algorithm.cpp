    //Can detect negative cycles

    int size = number_of_nodes;
    int start = starting_node;
    int end = ending_node;

    //edge list adjacency form where each edge is represented as (a, b, w) : starting node, ending node, weight/length of edge

    vvl edges; 

    //distance[x] = shortest distance of node x from starting node

    vl distance(size + 1, inf);  
    distance[start] = 0;

    // if number of nodes = n (size) : We do exactly n - 1 iterations
    //Why n - 1 ? because this algorithm is based on bfs approach i.e. it first updates only those distance vector values whose distance form starting node is 1, then in the 
    //next iteration it works for distance 2 and so on. Now this bfs approach would require n - 1 iterations in the worst case so as to explore all the levels

    forl(i, 1, size){
        fora(x, edges){
            if (distance[x[1]] > distance[x[0]] + x[2]){
                distance[x[1]] = distance[x[0]] + x[2];
            }
        }
    }

    //if it contains negative cycles then only it will update in this round

    int a = 0;
    fora(x, edges){
        if (distance[x[1]] > distance[x[0]] + x[2]){
            a++;
            break;
        }
    }
    if (a) cout<<-1;
    else cout<<distance[ending_node];

    //Time complexity = O(n*m)
