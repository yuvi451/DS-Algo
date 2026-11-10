# DSA Coaching Notes: question-by-question analysis of your sheet

**Source:** your "DSA" Google Sheet: all 214 rows of *All Tasks* (the *Today's Tasks* tab is the 3 revisions due 07-11-2026), all 40 linked Google Docs (20 were photos of handwritten notes or whiteboards, read as images), and the 15 C++ files the sheet links to in `yuvi451/DS-Algo`.
**Not reachable:** your private LeetCode submission links (they need your login), one Gemini share link, 3 YouTube videos.
**Link issues:** #190 "796. Rotate String" links to Valid Anagram; #52 links to a submission instead of the problem page. All other LeetCode/GFG/CSES links match their problem names.

## How to read the scores (1–10)
| Metric | What it measures |
|---|---|
| Pattern | Did you name the underlying technique, and why it applies? |
| Why | Can your notes justify correctness (invariants, proofs, counterexamples)? |
| Clarity | Could someone else rebuild the solution from your note alone? |
| Transfer | Do you connect it to related problems, or generalise a rule? |
| Edge | Edge cases and bug-awareness (from your notes and Revision Review) |
| Complexity | Time/space stated, brute force → optimal path, optimal reached? |
| Independence | From your status and time taken: E ≈ 8, H ≈ 5, S ≈ 3–4 |
| Retention | How likely you are to solve it cold in a month with these notes |

**Assumption:** I read Status as E = solved on your own, H = needed hints, S = studied the solution. This fits your revision gaps (E: 1 revision at +21 days; H: +3/+14/+42; S: +2/+7/+21/+61) and average times (E 26, H 35, S 54 minutes). Correct me if the codes mean something else.

## Scorecard by topic
| Topic | Questions | Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
| Sorting, Counting & CSES | 8 | 9.0 | 8.0 | 7.6 | 8.0 | 7.5 | 7.6 | 6.5 | 7.9 | **7.8** |
| Heaps | 4 | 9.0 | 7.8 | 7.2 | 8.0 | 7.8 | 7.0 | 6.5 | 8.0 | **7.7** |
| Arrays & Hashing | 22 | 8.8 | 8.0 | 7.6 | 8.5 | 7.5 | 7.4 | 5.0 | 8.2 | **7.6** |
| Binary Search Trees | 13 | 8.7 | 8.2 | 7.5 | 8.5 | 7.7 | 7.3 | 4.9 | 7.9 | **7.6** |
| Graphs | 22 | 8.8 | 7.7 | 7.1 | 8.5 | 7.3 | 7.1 | 6.4 | 7.8 | **7.6** |
| Two Pointers / Sliding Window | 14 | 8.9 | 7.6 | 7.3 | 8.4 | 7.6 | 7.7 | 5.1 | 8.0 | **7.6** |
| Greedy | 10 | 8.7 | 7.7 | 7.4 | 8.4 | 7.4 | 7.0 | 5.3 | 8.0 | **7.5** |
| Dynamic Programming | 30 | 8.7 | 7.4 | 6.9 | 8.5 | 7.3 | 6.9 | 6.1 | 7.6 | **7.5** |
| Binary Trees | 22 | 8.7 | 7.4 | 7.0 | 8.1 | 7.4 | 6.6 | 4.8 | 7.9 | **7.2** |
| Stacks, Queues & Monotonic Stack | 16 | 8.4 | 7.1 | 6.6 | 7.9 | 6.9 | 7.0 | 5.2 | 7.5 | **7.1** |
| Binary Search | 18 | 8.3 | 6.8 | 6.9 | 8.1 | 6.4 | 6.9 | 5.1 | 7.1 | **7.0** |
| Recursion & Backtracking | 12 | 8.3 | 7.4 | 7.2 | 7.8 | 7.0 | 5.9 | 4.6 | 7.3 | **6.9** |
| Linked List | 15 | 8.2 | 6.5 | 6.3 | 7.2 | 6.6 | 6.7 | 4.9 | 7.3 | **6.7** |
| Strings | 8 | 8.0 | 5.2 | 5.1 | 6.9 | 7.0 | 5.9 | 7.2 | 6.4 | **6.5** |
| **All 214** | 214 | 8.6 | 7.4 | 7.0 | 8.1 | 7.2 | 7.0 | 5.5 | 7.7 | **7.3** |

## Index of all 214 questions
| # | Problem | Section | Status | Min | Overall |
|---|---|---|---|---|---|
| 1 | 33. Search in Rotated Sorted Array | Binary Search | S | 30 | 7.4 |
| 2 | 81. Search in Rotated Sorted Array II | Binary Search | S | 40 | 6.8 |
| 3 | 540. Single Element in a Sorted Array | Binary Search | H | 40 | 5.4 |
| 4 | 162. Find Peak Element | Binary Search | E | 25 | 6.1 |
| 5 | Nth root of a number | Binary Search | H | 15 | 6.0 |
| 6 | 1539. Kth Missing Positive Number | Binary Search | H | 30 | 6.6 |
| 7 | Aggresive Cows | Binary Search | S | 30 | 7.5 |
| 8 | Allocate Minimum pages | Binary Search | E | 40 | 7.8 |
| 9 | Painter's Partition Problem | Binary Search | H | 30 | 6.6 |
| 10 | Minimize Max Distance to Gas Station | Binary Search | S | 60 | 7.1 |
| 11 | 4. Median of Two Sorted Arrays | Binary Search | S | 60 | 7.0 |
| 12 | K-th element of two Arrays | Binary Search | H | 30 | 7.4 |
| 13 | 74. Search a 2D Matrix | Binary Search | H | 15 | 6.6 |
| 14 | 240. Search a 2D Matrix II | Binary Search | S | 20 | 7.6 |
| 15 | 1901. Find a Peak Element II | Binary Search | S | 40 | 6.9 |
| 16 | Median in a row-wise sorted Matrix | Binary Search | S | 40 | 6.6 |
| 17 | 206. Reverse Linked List | Linked List | E | 20 | 7.9 |
| 18 | 142. Linked List Cycle II | Linked List | S | 20 | 7.8 |
| 19 | 234. Palindrome Linked List | Linked List | H | 30 | 6.1 |
| 20 | 328. Odd Even Linked List | Linked List | H | 30 | 7.0 |
| 21 | 19. Remove Nth Node From End of List | Linked List | E | 15 | 6.6 |
| 22 | 148. Sort List | Linked List | H | 40 | 6.9 |
| 23 | Sort a linked list of 0s, 1s and 2s | Linked List | H | 50 | 6.6 |
| 24 | 160. Intersection of Two Linked Lists | Linked List | S | 60 | 7.2 |
| 25 | Add 1 to a Linked List Number | Linked List | H | 20 | 4.4 |
| 26 | 2. Add Two Numbers | Linked List | H | 30 | 6.1 |
| 27 | Delete all occurrences in a doubly linked list | Linked List | H | 40 | 5.8 |
| 28 | 25. Reverse Nodes in k-Group | Linked List | S | 70 | 6.1 |
| 29 | Flattening a Linked List | Linked List | H | 30 | 7.4 |
| 30 | 138. Copy List with Random Pointer | Linked List | S | 70 | 7.6 |
| 31 | 22. Generate Parentheses | Recursion & Backtracking | H | 40 | 7.8 |
| 32 | Subsequence with Sum K | Recursion & Backtracking | H | 40 | 6.9 |
| 33 | 78. Subsets | Recursion & Backtracking | H | 30 | 7.4 |
| 34 | 90. Subsets II | Recursion & Backtracking | S | 60 | 7.5 |
| 35 | 40. Combination Sum II | Recursion & Backtracking | H | 20 | 5.4 |
| 36 | 131. Palindrome Partitioning | Recursion & Backtracking | H | 30 | 6.9 |
| 37 | 79. Word Search | Recursion & Backtracking | S | 60 | 6.4 |
| 38 | 51. N-Queens | Recursion & Backtracking | S | 60 | 7.8 |
| 39 | 139. Word Break | Recursion & Backtracking | H | 40 | 7.5 |
| 40 | 282. Expression Add Operators | Recursion & Backtracking | S | 120 | 7.0 |
| 41 | 37. Sudoku Solver | Recursion & Backtracking | H | 50 | 6.4 |
| 42 | M-Coloring Problem | Recursion & Backtracking | S | 50 | 6.6 |
| 43 | 20. Valid Parentheses | Stacks, Queues & Monotonic Stack | H | 20 | 6.6 |
| 44 | 155. Min Stack | Stacks, Queues & Monotonic Stack | S | 40 | 7.4 |
| 45 | NGE/PGE | Stacks, Queues & Monotonic Stack | H | 40 | 7.4 |
| 46 | 503. Next Greater Element II | Stacks, Queues & Monotonic Stack | H | 40 | 6.5 |
| 47 | Number of greater elements to the right | Stacks, Queues & Monotonic Stack | S | 120 | 7.4 |
| 48 | 42. Trapping Rain Water | Stacks, Queues & Monotonic Stack | S | 40 | 7.5 |
| 49 | 907. Sum of Subarray Minimums | Stacks, Queues & Monotonic Stack | H | 40 | 8.0 |
| 50 | 735. Asteroid Collision | Stacks, Queues & Monotonic Stack | H | 30 | 6.8 |
| 51 | 2104. Sum of Subarray Ranges | Stacks, Queues & Monotonic Stack | H | 40 | 7.1 |
| 52 | 402. Remove K Digits | Stacks, Queues & Monotonic Stack | H | 50 | 7.0 |
| 53 | 84. Largest Rectangle in Histogram | Stacks, Queues & Monotonic Stack | H | 30 | 7.6 |
| 54 | 85. Maximal Rectangle | Stacks, Queues & Monotonic Stack | E | 30 | 7.5 |
| 55 | 239. Sliding Window Maximum | Stacks, Queues & Monotonic Stack | S | 50 | 7.6 |
| 56 | 901. Online Stock Span | Stacks, Queues & Monotonic Stack | H | 40 | 6.4 |
| 57 | The Celebrity Problem | Two Pointers / Sliding Window | S | 30 | 7.6 |
| 58 | 146. LRU Cache | Linked List | S | 120 | 7.2 |
| 59 | 102. Binary Tree Level Order Traversal | Binary Trees | S | 40 | 7.1 |
| 60 | All Traversals (Pre, In, Post) | Binary Trees | S | 70 | 7.8 |
| 61 | 104. Maximum Depth of Binary Tree | Binary Trees | H | 20 | 7.2 |
| 62 | 110. Balanced Binary Tree | Binary Trees | H | 20 | 6.4 |
| 63 | 543. Diameter of Binary Tree | Binary Trees | H | 20 | 7.9 |
| 64 | 124. Binary Tree Maximum Path Sum | Binary Trees | H | 50 | 7.8 |
| 65 | Tree Boundary Traversal | Binary Trees | H | 50 | 7.0 |
| 66 | 987. Vertical Order Traversal of a Binary Tree | Binary Trees | S | 60 | 7.2 |
| 67 | 101. Symmetric Tree | Binary Trees | E | 15 | 6.6 |
| 68 | Top/ Bottom View of Binary Tree | Binary Trees | H | 25 | 7.2 |
| 69 | 199. Binary Tree Right Side View | Binary Trees | H | 10 | 6.8 |
| 70 | 662. Maximum Width of Binary Tree | Binary Trees | H | 60 | 7.9 |
| 71 | 236. Lowest Common Ancestor of a Binary Tree | Binary Trees | S | 50 | 8.1 |
| 72 | Children Sum in a Binary Tree | Binary Trees | H | 15 | 6.5 |
| 73 | 863. All Nodes Distance K in Binary Tree | Binary Trees | H | 40 | 7.2 |
| 74 | 222. Count Complete Tree Nodes | Binary Trees | H | 30 | 7.8 |
| 75 | 105. Construct Binary Tree from Preorder and Inorder Traversal | Binary Trees | S | 60 | 8.0 |
| 76 | 106. Construct Binary Tree from Inorder and Postorder Traversal | Binary Trees | H | 20 | 7.0 |
| 77 | 114. Flatten Binary Tree to Linked List | Binary Trees | H | 40 | 6.2 |
| 78 | 297. Serialize and Deserialize Binary Tree | Binary Trees | H | 60 | 6.1 |
| 79 | 94. Binary Tree Inorder Traversal | Binary Trees | S | 60 | 8.5 |
| 80 | Floor and Ceil in a BST | Binary Search Trees | E | 20 | 7.1 |
| 81 | 450. Delete Node in a BST | Binary Search Trees | S | 40 | 8.4 |
| 82 | 701. Insert into a Binary Search Tree | Binary Search Trees | H | 20 | 7.2 |
| 83 | 230. Kth Smallest Element in a BST | Binary Search Trees | H | 30 | 8.1 |
| 84 | 235. Lowest Common Ancestor of a Binary Search Tree | Binary Search Trees | H | 20 | 7.6 |
| 85 | 1008. Construct Binary Search Tree from Preorder Traversal | Binary Search Trees | H | 30 | 6.8 |
| 86 | Predecessor and Successor | Binary Search Trees | E | 20 | 7.6 |
| 87 | Merge two BSTs to form a single BST | Binary Search Trees | H | 40 | 7.1 |
| 88 | 98. Validate Binary Search Tree | Binary Search Trees | H | 30 | 7.9 |
| 89 | 1373. Maximum Sum BST in Binary Tree | Binary Search Trees | S | 90 | 8.1 |
| 90 | 99. Recover Binary Search Tree | Binary Search Trees | H | 60 | 8.2 |
| 91 | 653. Two Sum IV - Input is a BST | Binary Search Trees | H | 40 | 7.5 |
| 92 | 1932. Merge BSTs to Create Single BST | Binary Search Trees | S | 120 | 7.0 |
| 93 | Undirected Graph Cycle | Graphs | E | 20 | 7.6 |
| 94 | Directed Graph Cycle | Graphs | E | 20 | 7.4 |
| 95 | 127. Word Ladder | Graphs | E | 40 | 7.8 |
| 96 | 126. Word Ladder II | Graphs | H | 120 | 7.9 |
| 97 | Topological Sorting | Graphs | E | 30 | 8.4 |
| 98 | 802. Find Eventual Safe States | Graphs | H | 30 | 7.9 |
| 99 | Alien Dictionary | Graphs | H | 40 | 7.6 |
| 100 | Shortest Paths | Graphs | E | 30 | 8.5 |
| 101 | 1631. Path With Minimum Effort | Graphs | E | 20 | 7.1 |
| 102 | 787. Cheapest Flights Within K Stops | Graphs | H | 40 | 8.4 |
| 103 | 1976. Number of Ways to Arrive at Destination | Graphs | H | 30 | 8.0 |
| 104 | Minimum Multiplications to reach End | Graphs | E | 20 | 7.6 |
| 105 | MST | Graphs | E | 20 | 7.5 |
| 106 | 1319. Number of Operations to Make Network Connected | Graphs | E | 20 | 5.4 |
| 107 | 947. Most Stones Removed with Same Row or Column | Graphs | H | 30 | 5.8 |
| 108 | 721. Accounts Merge | Graphs | H | 60 | 7.5 |
| 109 | Number Of Islands | Graphs | S | 60 | 7.6 |
| 110 | 827. Making A Large Island | Graphs | H | ? | 7.6 |
| 111 | 778. Swim in Rising Water | Graphs | E | 20 | 6.9 |
| 112 | Strongly Connected Components (SCC) | Graphs | E | 60 | 8.8 |
| 113 | Bridges in a graph | Graphs | H | 30 | 8.1 |
| 114 | Articulation Points | Graphs | H | 30 | 7.8 |
| 115 | 2498. Frog Jump II | Greedy | H | 30 | 6.4 |
| 116 | 198. House Robber | Dynamic Programming | H | 20 | 7.8 |
| 117 | 213. House Robber II | Dynamic Programming | H | 20 | 6.6 |
| 118 | 337. House Robber III | Binary Trees | S | 30 | 7.1 |
| 119 | 1463. Cherry Pickup II | Dynamic Programming | E | 30 | 8.0 |
| 120 | 494. Target Sum | Dynamic Programming | E | 30 | 7.2 |
| 121 | 416. Partition Equal Subset Sum | Dynamic Programming | E | 40 | 6.0 |
| 122 | 2035. Partition Array Into Two Arrays to Minimize Sum Difference | Dynamic Programming | H | 50 | 8.0 |
| 123 | Count Subsets with Sum | Dynamic Programming | E | 20 | 6.5 |
| 124 | Partitions with Given Difference | Dynamic Programming | E | 30 | 7.4 |
| 125 | 322. Coin Change | Dynamic Programming | E | 20 | 8.1 |
| 126 | Coin Combinations II | Dynamic Programming | H | 30 | 7.8 |
| 127 | Rod Cutting | Dynamic Programming | H | 30 | 7.5 |
| 128 | Print Longest Common Subsequence | Dynamic Programming | E | 30 | 8.1 |
| 129 | 1312. Minimum Insertion Steps to Make a String Palindrome | Dynamic Programming | E | 30 | 6.5 |
| 130 | 1092. Shortest Common Supersequence | Dynamic Programming | E | 20 | 7.6 |
| 131 | 115. Distinct Subsequences | Dynamic Programming | H | 40 | 7.8 |
| 132 | 44. Wildcard Matching | Dynamic Programming | H | 40 | 7.8 |
| 133 | 188. Best Time to Buy and Sell Stock IV | Dynamic Programming | H | 40 | 8.0 |
| 134 | 714. Best Time to Buy and Sell Stock with Transaction Fee | Dynamic Programming | H | 10 | 7.0 |
| 135 | 122. Best Time to Buy and Sell Stock II | Dynamic Programming | E | 20 | 6.1 |
| 136 | 368. Largest Divisible Subset | Dynamic Programming | H | 30 | 7.6 |
| 137 | 1048. Longest String Chain | Dynamic Programming | H | 30 | 7.6 |
| 138 | Longest Bitonic Subsequence | Dynamic Programming | E | 20 | 7.9 |
| 139 | Matrix Chain Multiplication | Dynamic Programming | H | 30 | 7.6 |
| 140 | 1547. Minimum Cost to Cut a Stick | Dynamic Programming | H | 30 | 7.9 |
| 141 | 312. Burst Balloons | Dynamic Programming | S | 120 | 7.8 |
| 142 | 1106. Parsing A Boolean Expression | Stacks, Queues & Monotonic Stack | E | 20 | 6.9 |
| 143 | 132. Palindrome Partitioning II | Dynamic Programming | H | 40 | 7.5 |
| 144 | 1277. Count Square Submatrices with All Ones | Dynamic Programming | E | 30 | 6.9 |
| 145 | 189. Rotate Array | Arrays & Hashing | E | 20 | 6.6 |
| 146 | 283. Move Zeroes | Arrays & Hashing | H | 20 | 6.6 |
| 147 | Longest Subarray with Sum K | Arrays & Hashing | H | 30 | 7.6 |
| 148 | 560. Subarray Sum Equals K | Arrays & Hashing | H | 30 | 8.1 |
| 149 | 53. Maximum Subarray | Arrays & Hashing | H | 40 | 8.1 |
| 150 | 75. Sort Colors | Arrays & Hashing | S | 40 | 8.2 |
| 151 | 169. Majority Element | Arrays & Hashing | S | 20 | 7.5 |
| 152 | 47. Permutations II | Arrays & Hashing | H | 30 | 8.0 |
| 153 | 31. Next Permutation | Arrays & Hashing | S | 30 | 7.2 |
| 154 | 128. Longest Consecutive Sequence | Arrays & Hashing | H | 30 | 7.9 |
| 155 | 54. Spiral Matrix | Arrays & Hashing | H | 30 | 6.8 |
| 156 | 48. Rotate Image | Arrays & Hashing | H | 20 | 7.8 |
| 157 | 73. Set Matrix Zeroes | Arrays & Hashing | H | 40 | 7.6 |
| 158 | 15. 3Sum | Arrays & Hashing | S | 40 | 8.0 |
| 159 | 18. 4Sum | Arrays & Hashing | H | 20 | 7.2 |
| 160 | 229. Majority Element II | Arrays & Hashing | S | 40 | 8.4 |
| 161 | Count Subarrays with given XOR | Arrays & Hashing | E | 20 | 7.8 |
| 162 | 2588. Count the Number of Beautiful Subarrays | Arrays & Hashing | H | 30 | 8.0 |
| 163 | Missing And Repeating | Arrays & Hashing | H | 40 | 6.9 |
| 164 | 56. Merge Intervals | Arrays & Hashing | H | 40 | 7.5 |
| 165 | 493. Reverse Pairs | Arrays & Hashing | S | 50 | 8.0 |
| 166 | 152. Maximum Product Subarray | Arrays & Hashing | H | 30 | 7.9 |
| 167 | T - Permutation | Dynamic Programming | H | 40 | 7.9 |
| 168 | 55. Jump Game | Greedy | H | 20 | 7.6 |
| 169 | 45. Jump Game II | Greedy | S | 50 | 7.8 |
| 170 | 678. Valid Parenthesis String | Greedy | S | 40 | 8.2 |
| 171 | 135. Candy | Greedy | S | 30 | 8.2 |
| 172 | Minimum Platforms | Greedy | H | 30 | 7.5 |
| 173 | Job Sequencing Problem | Greedy | H | 50 | 7.8 |
| 174 | 57. Insert Interval | Greedy | E | 30 | 6.0 |
| 175 | 435. Non-overlapping Intervals | Greedy | H | 30 | 7.9 |
| 176 | 1235. Maximum Profit in Job Scheduling | Dynamic Programming | H | 40 | 7.9 |
| 177 | 3. Longest Substring Without Repeating Characters | Two Pointers / Sliding Window | E | 20 | 5.9 |
| 178 | 1004. Max Consecutive Ones III | Two Pointers / Sliding Window | H | 30 | 7.4 |
| 179 | 904. Fruit Into Baskets | Two Pointers / Sliding Window | H | 20 | 7.4 |
| 180 | 1248. Count Number of Nice Subarrays | Two Pointers / Sliding Window | H | 40 | 7.4 |
| 181 | 930. Binary Subarrays With Sum | Two Pointers / Sliding Window | S | 40 | 8.1 |
| 182 | Longest Substring with K Uniques | Two Pointers / Sliding Window | H | 20 | 7.4 |
| 183 | 1423. Maximum Points You Can Obtain from Cards | Two Pointers / Sliding Window | E | 20 | 7.8 |
| 184 | 992. Subarrays with K Different Integers | Two Pointers / Sliding Window | H | 30 | 8.0 |
| 185 | 1358. Number of Substrings Containing All Three Characters | Two Pointers / Sliding Window | H | 30 | 7.9 |
| 186 | 424. Longest Repeating Character Replacement | Two Pointers / Sliding Window | S | 40 | 8.2 |
| 187 | 76. Minimum Window Substring | Two Pointers / Sliding Window | S | 40 | 7.8 |
| 188 | Minimum Window Subsequence | Two Pointers / Sliding Window | S | 40 | 7.4 |
| 189 | 205. Isomorphic Strings | Strings | E | 10 | 7.2 |
| 190 | 796. Rotate String | Strings | E | 20 | 5.0 |
| 191 | 451. Sort Characters By Frequency | Strings | E | 10 | 5.1 |
| 192 | 5. Longest Palindromic Substring | Strings | H | 30 | 7.5 |
| 193 | 1781. Sum of Beauty of All Substrings | Strings | E | 30 | 6.6 |
| 194 | 921. Minimum Add to Make Parentheses Valid | Strings | H | 20 | 7.9 |
| 195 | 38. Count and Say | Strings | E | 10 | 6.2 |
| 196 | Count Palindromic Subsequences | Dynamic Programming | H | 40 | 7.4 |
| 197 | Minimum Cost to Make Pods Distinct | Heaps | H | 60 | 7.6 |
| 198 | 215. Kth Largest Element in an Array | Heaps | E | 20 | 8.0 |
| 199 | 1297. Maximum Number of Occurrences of a Substring | Two Pointers / Sliding Window | H | 40 | 8.0 |
| 200 | Minimize GPU Idle Count | Binary Search | E | 40 | 7.8 |
| 201 | Minimum Tree Height After At Most K Operations | Binary Search | H | 60 | 8.0 |
| 202 | Minimum Deletion Span to Make a Subsequence | Strings | E | 30 | 6.1 |
| 203 | 621. Task Scheduler | Heaps | H | 60 | 7.4 |
| 204 | 846. Hand of Straights | Greedy | E | 30 | 7.5 |
| 205 | Concert Tikcets | Sorting, Counting & CSES | H | 40 | 7.8 |
| 206 | Missing Coin Sum | Sorting, Counting & CSES | H | 40 | 7.9 |
| 207 | Traffic Lights | Sorting, Counting & CSES | E | 30 | 8.1 |
| 208 | Josephus Problem I | Stacks, Queues & Monotonic Stack | E | 30 | 5.6 |
| 209 | Distinct Values Subsequences | Sorting, Counting & CSES | H | 30 | 7.5 |
| 210 | Collecting Numbers II | Sorting, Counting & CSES | E | 40 | 7.6 |
| 211 | Nested Ranges Check | Sorting, Counting & CSES | H | 60 | 7.6 |
| 212 | Room Allocation | Heaps | E | 30 | 7.6 |
| 213 | Tasks and Deadlines | Sorting, Counting & CSES | E | 40 | 7.9 |
| 214 | Reading Books | Sorting, Counting & CSES | E | 30 | 7.8 |

# Question-by-question notes

## Binary Search

### #1 · 33. Search in Rotated Sorted Array
*Sheet: 20-05-2026 · Topic: Binary Search · Pattern: Binary Search in Rotated Array · Difficulty M · Status S · 30 min · 4 revisions scheduled*
**Your thinking:** In a rotated array one of the two halves around mid is always sorted. In the sorted half you can tell for sure whether the target can be there, so you either go into it or discard it. You reduced it to one rule: find the sorted part, then decide inside it.
**Coach:** The right core idea, written so it carries over to other problems (it is why #2 went quickly). Be ready to explain why the check is `nums[low] <= nums[mid]` and not `<` (when low == mid the left part has one element).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 7 | 7 | 4 | 8 | **7.4** |

### #2 · 81. Search in Rotated Sorted Array II
*Sheet: 20-05-2026 · Topic: Binary Search · Pattern: Binary Search in Rotated Array with duplicates · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Same as #1, but with duplicates: when low, mid and high are all equal you can't tell which half is sorted, so you shrink both ends. You also noted to check `nums[mid] == target` first.
**Coach:** Good ordering of the checks. Your notes don't mention that the worst case becomes O(n) (e.g. `[1,1,1,1,2,1,1]`); interviewers ask about this. Listing related variants (minimum of a rotated array, number of rotations) is good.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 8 | 8 | 5 | 4 | 7 | **6.8** |

### #3 · 540. Single Element in a Sorted Array
*Sheet: 20-05-2026 · Topic: Binary Search · Pattern: Single element in sorted array · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** You use index parity. Before the single element, pairs sit at (even, odd) indices; after it, at (odd, even). You handle index 0 and n−1 separately and search the rest.
**Coach:** You memorised the parity pattern ("just remember") rather than deriving it. Your revision note says you forgot to check whether mid itself is the answer, and the same mistake shows up again in #4. Make it a standard step: before moving low or high, ask "could mid be the answer?"
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 7 | 5 | 6 | 6 | 4 | 5 | 5 | 5 | **5.4** |

### #4 · 162. Find Peak Element
*Sheet: 20-05-2026 · Topic: Binary Search · Pattern: Find peak element · Difficulty M · Status E · 25 min · 1 revisions scheduled*
**Your thinking:** You handle the two ends separately, then follow the slope: if `nums[mid] > nums[mid-1]`, you are going uphill, so a peak exists on the right.
**Coach:** Right idea: binary search on a slope rather than on sorted values. The revision note again says you forgot to check mid, so this is a habit, not a one-off. You marked it E with one revision even though the error repeated; I would schedule another revision.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 7 | 4 | 6 | 7 | 5 | **6.1** |

### #5 · Nth root of a number (GFG)
*Sheet: 21-05-2026 · Topic: Binary Search · Pattern: Find n-th root upto a certain precision using BS · Difficulty - · Status H · 15 min · 3 revisions scheduled*
**Your thinking:** Binary search over real numbers, looping `while (high - low > eps)` because low and high may never become exactly equal.
**Coach:** The precision loop is a useful tool, and you used it again in #10. But the GFG problem asks for an integer root (or −1). The intended solution is integer binary search with a power function that stops early once the product exceeds m, so it can't overflow. Your note only covers the real-number version.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 7 | 5 | 6 | 7 | 5 | 6 | 6 | 6 | **6.0** |

### #6 · 1539. Kth Missing Positive Number
*Sheet: 21-05-2026 · Topic: Binary Search · Pattern: Binary search on missing number · Difficulty E · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** You found the key count: before index mid there are `arr[mid] - mid - 1` missing numbers. Because this count only grows, you binary search for the last index with fewer than k missing, and handle "the answer is before arr[0]" separately.
**Coach:** Good: you turned a count into a yes/no condition you can binary search on. Learn the closed form `answer = low + k` after the loop; it handles your idx == 0 case without a special branch.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 7 | 6 | 6 | 5 | 7 | **6.6** |

### #7 · Aggressive Cows
*Sheet: 21-05-2026 · Topic: Binary Search · Pattern: max of min · Difficulty M · Status S · 30 min · 4 revisions scheduled*
**Your thinking:** You noticed the answers are monotonic: every distance up to some point works and nothing beyond it does. So you binary search on the distance, and for each guess a greedy left-to-right placement checks whether all cows fit. Sort first; low = 1, high = max − min.
**Coach:** A strong explanation of "binary search on the answer", including why it is allowed. Calling the greedy check "two pointers" isn't quite right (it is a single greedy scan), but your "allocation problem" label is a good umbrella for the family.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 7 | 7 | 4 | 8 | **7.5** |

### #8 · Allocate Minimum Pages
*Sheet: 22-05-2026 · Topic: Binary Search · Pattern: min of max · Difficulty M · Status E · 40 min · 1 revisions scheduled*
**Your thinking:** You carried the max-of-min idea over to min-of-max: binary search on the most pages one student gets, greedily count how many students that needs, and check the count is at most k. You noted adding one at the end for the last group, and returning −1 when k > n.
**Coach:** A clean, quick transfer (E, 40 min). Make sure you can explain why low must start at max(arr) and not at 1.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 7 | 8 | 8 | **7.8** |

### #9 · Painter's Partition
*Sheet: 22-05-2026 · Topic: Binary Search · Pattern: min of max · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** You recognised it as the same problem as #8.
**Coach:** Recognising that is the real skill here. But the note says only "initialise low and high properly" without saying what they are. Write the actual values (max board length, total length) so revision doesn't depend on memory.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 5 | 5 | 9 | 6 | 6 | 6 | 7 | **6.6** |

### #10 · Minimize Max Distance to Gas Station
*Sheet: 22-05-2026 · Topic: Binary Search · Pattern: min of max · Difficulty H · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** Your doc climbs from slow to fast. (1) Place stations one at a time, each in the current largest gap: O(K·n). (2) Use a priority queue to find the largest gap: O(K log n). (3) Binary search on the answer over doubles: for a gap and a guessed distance, count how many stations it needs, subtracting one when the gap divides exactly. You noted low = 0 because the answer can be fractional.
**Coach:** One of your best notes: three approaches and a clear explanation of why this differs from the allocation problems. Your revision note admits you mixed it up with those problems and forgot the double-precision updates. Comparing floating-point numbers with `p*mid == gap` is fragile; use `ceil(gap/mid) - 1` instead.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 8 | 8 | 8 | 5 | 9 | 4 | 7 | **7.1** |

### #11 · 4. Median of Two Sorted Arrays
*Sheet: 23-05-2026 · Topic: Binary Search · Pattern: median of two sorted arrays · Difficulty H · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** Binary search on how many elements you take from the smaller array; the rest of the left half comes from the other array. You check `l1 <= r2 && l2 <= r1`, use INT_MIN/INT_MAX for empty sides, and handle odd and even totals. Your revision note gives the clean bounds `low = max(0, k−n2), high = min(k, n1)`.
**Coach:** A complete, step-by-step explanation; the bounds formula is something many people never learn. You picked it up from a video (S, 60 min); check you can rebuild it without notes.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 8 | 8 | 7 | 8 | 3 | 7 | **7.0** |

### #12 · K-th element of two Arrays
*Sheet: 23-05-2026 · Topic: Binary Search · Pattern: k-th element of two sorted arrays · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** You reused #11 with general k and the same bounds formula instead of swapping arrays.
**Coach:** A good example of you generalising an idea yourself. The note is short, but the problem really is just #11 with k as a parameter.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 6 | 9 | 7 | 7 | 6 | 8 | **7.4** |

### #13 · 74. Search a 2D Matrix
*Sheet: 24-05-2026 · Topic: Binary Search · Pattern: flattening of 2d matrix · Difficulty M · Status H · 15 min · 3 revisions scheduled*
**Your thinking:** Treat the matrix as one flat sorted array and map index mid to `(mid / n, mid % n)`. Only the number of columns matters.
**Coach:** Correct. Your note writes `x = mid % n, y = mid / n` without saying which is the row; say it explicitly (row = mid / n).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 7 | 7 | 7 | 5 | 7 | **6.6** |

### #14 · 240. Search a 2D Matrix II
*Sheet: 25-05-2026 · Topic: Binary Search/ Two Pointers · Pattern: BS: Better, Two pointers: Optimal · Difficulty M · Status S · 20 min · 4 revisions scheduled*
**Your thinking:** Binary searching each row gives O(n log m), but starting from the top-right (or bottom-left) corner lets you rule out a whole row or column each step, giving O(n + m).
**Coach:** You explained the reason (those corners are the only places where one direction goes up and the other goes down) and compared both approaches. Strong.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 7 | 9 | 4 | 8 | **7.6** |

### #15 · 1901. Find a Peak Element II
*Sheet: 25-05-2026 · Topic: Binary Search · Pattern: Find peak element in 2D matrix · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Binary search on columns. In the middle column take the largest value; if a neighbour beside it is bigger, move to that side. That side must contain a peak, so you can throw away the other half.
**Coach:** A good extension of #4 to two dimensions, and you remembered the out-of-range neighbour guard. Add the complexity: O(n log m).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 9 | 7 | 6 | 4 | 7 | **6.9** |

### #16 · Median in a Row-wise Sorted Matrix
*Sheet: 25-05-2026 · Topic: Binary Search · Pattern: Median in a row vise sorted matrix · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Binary search on the value: for each guess, count elements ≤ it using binary search in each row, and find the smallest value with enough elements below it. Complexity log(range) · n · log m.
**Coach:** A good "binary search on the value" pattern. Your stopping condition ("at least m·n/2 elements less than it") is loosely worded; the exact version is the smallest x with count(≤ x) > (m·n)/2.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 8 | 6 | 8 | 4 | 7 | **6.6** |

### #200 · Minimize GPU Idle Count (custom problem)
*Sheet: 09-10-2026 · Topic: Binary Search · Pattern: minimize max consective characters · Difficulty M · Status E · 40 min · 1 revisions scheduled*
**Your thinking:** Binary search on the longest allowed run of the same letter. For each run of length L you need `L / (mid + 1)` flips. You handle mid = 1 (an alternating string) separately and search from 2 to n.
**Coach:** Recognising the monotonic condition in an unfamiliar problem is the skill that matters on new problems. The flip count per run, `L / (mid+1)`, is the key insight. Solved independently (E), which shows binary search on the answer is now natural for you.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 7 | 8 | 8 | **7.8** |

### #201 · Minimum Tree Height After At Most K Operations (custom)
*Sheet: 11-10-2026 · Topic: Binary Search + Trees · Pattern: find minimum height of tree after atmost K operations · Difficulty H · Status H · 60 min · 3 revisions scheduled*
**Your thinking:** Binary search on the target height. To check one, go bottom-up and cut the highest subtree that still fits once it is reattached under the root (`height == target − 1`), counting cuts. A depth guard stops you cutting the root or its direct children.
**Coach:** Excellent: you justified the bottom-up greedy, kept the depth guard and gave the complexity. This is the kind of thinking you need for new problems.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 8 | 5 | 8 | **8.0** |

## Linked List

### #17 · 206. Reverse Linked List
*Sheet: 28-05-2026 · Topic: LinkedList · Pattern: Reverse a single LL (recursive + iterative) · Difficulty E · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Iteratively with three pointers, and recursively: reverse the rest of the list, then `head->next->next = head; head->next = NULL`. Lesson: draw it on paper.
**Coach:** Your recursive explanation is careful, including why head->next still points to the right node. Basic, but your understanding is solid.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 7 | 8 | 7 | 8 | 9 | **7.9** |

### #18 · 142. Linked List Cycle II
*Sheet: 29-05-2026 · Topic: LinkedList · Pattern: Find node from which cycle starts · Difficulty M · Status S · 20 min · 4 revisions scheduled*
**Your thinking:** Floyd's algorithm: wait for the slow and fast pointers to meet, then move one back to the head and step both one at a time until they meet again. You proved it on paper (x = n·c − d, so x = (n−1)·c + y).
**Coach:** Your own proof, not a memorised trick. The "set visited nodes to INT_MAX" hack changes the input; you rightly called it a last resort.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 8 | 7 | 4 | 9 | **7.8** |

### #19 · 234. Palindrome Linked List
*Sheet: 29-05-2026 · Topic: LinkedList · Pattern: check if pallindrome · Difficulty E · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Find the middle, reverse the second half, compare the halves.
**Coach:** Correct but only a one-line note. Add: reverse the second half back afterwards (leave the input unchanged), and how to find the middle for odd and even lengths.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 5 | 7 | 6 | 6 | 5 | 7 | **6.1** |

### #20 · 328. Odd Even Linked List
*Sheet: 29-05-2026 · Topic: LinkedList · Pattern: Segregating odd and even elements · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Build separate odd and even lists with dummy heads, then join them. You found that ending the even list with NULL is what prevents a cycle.
**Coach:** You worked out the cycle bug yourself, which is real debugging insight. The dummy-head approach is the reusable takeaway.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 8 | 7 | 7 | 5 | 7 | **7.0** |

### #21 · 19. Remove Nth Node From End of List
*Sheet: 29-05-2026 · Topic: LinkedList · Pattern: delete n-th node from end; TWO POINTERS + LL · Difficulty M · Status E · 15 min · 1 revisions scheduled*
**Your thinking:** Two pointers spaced n apart; be careful when the head itself is removed.
**Coach:** Quick (E, 15 min). Putting a dummy node before the head removes the head special case completely; use that as your default.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 5 | 7 | 6 | 7 | 8 | 7 | **6.6** |

### #22 · 148. Sort List
*Sheet: 30-05-2026 · Topic: LinkedList · Pattern: sort a LL using merge sort · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Merge sort: find the middle with slow and fast pointers, cut the list at the node before the middle, sort both halves, merge. When merging, detach each node before linking it.
**Coach:** Good recursive framing. Note it uses O(log n) stack space; bottom-up merge sort is the O(1)-space follow-up.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 8 | 7 | 6 | 5 | 7 | **6.9** |

### #23 · Sort a linked list of 0s, 1s and 2s
*Sheet: 30-05-2026 · Topic: LinkedList · Pattern: segregate 0s, 1s, 2s of LL · Difficulty M · Status H · 50 min · 3 revisions scheduled*
**Your thinking:** Not the Dutch National Flag algorithm: make three lists and join them, just like odd/even. Draw it on paper; detach nodes before joining.
**Coach:** Good transfer from #20. Taking 50 minutes on a medium shows linking pointers is still error-prone for you; it's an implementation issue, not a gap in understanding.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 8 | 6 | 7 | 5 | 7 | **6.6** |

### #24 · 160. Intersection of Two Linked Lists
*Sheet: 30-05-2026 · Topic: LinkedList · Pattern: find the intersection point · Difficulty M · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** Method 1: find both lengths and move the longer list's pointer ahead by the difference. Method 2: when a pointer reaches the end, restart it at the other list's head; both travel x + y + z steps and meet. You proved both on paper.
**Coach:** Two methods, both proved. It took 60 minutes (S), but the doc shows real understanding.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 7 | 7 | 8 | 4 | 8 | **7.2** |

### #25 · Add 1 to a Linked List Number
*Sheet: 30-05-2026 · Topic: LinkedList · Pattern: add 1 to a number represented by LL · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Your note is only the digit formula `(data + carry) % 10`.
**Coach:** Too thin to show how you handle it. The real choices are: reverse, add, reverse back; or recurse to the end and return the carry. Also the "999 → 1000" case where a new head is needed. Rewrite the note.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 6 | 3 | 3 | 5 | 5 | 4 | 5 | 4 | **4.4** |

### #26 · 2. Add Two Numbers
*Sheet: 30-05-2026 · Topic: LinkedList · Pattern: add any two numbers using LL · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Build a new list with a running carry; the digits are already reversed.
**Coach:** Fine. Your note "you'd have to reverse first otherwise" links it to #25, which is good transfer.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 5 | 7 | 6 | 6 | 5 | 7 | **6.1** |

### #27 · Delete all occurrences in a doubly linked list
*Sheet: 30-05-2026 · Topic: LinkedList · Pattern: delete all occurances in a dll · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Handle the head, middle and tail separately with prev and next pointers, and check for NULL everywhere.
**Coach:** It works, but a dummy head would remove most of the special cases. You learned dummy nodes in #20 but didn't use them here.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 7 | 5 | 6 | 5 | 6 | 6 | 5 | 6 | **5.8** |

### #28 · 25. Reverse Nodes in k-Group
*Sheet: 31-07-2026 · Topic: LinkedList · Pattern: reverse in groups of K · Difficulty H · Status S · 70 min · 4 revisions scheduled*
**Your thinking:** Reverse k nodes, then reconnect the group's start and end to the rest using four pointers (sketched on paper). The logic was easy; the wiring was hard (70 min). Lesson: settle the approach on paper before coding.
**Coach:** Your self-assessment is accurate. The four-pointer sketch is the right tool; keep it as your template.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 7 | 6 | 6 | 3 | 7 | **6.1** |

### #29 · Flattening a Linked List
*Sheet: 31-05-2026 · Topic: LinkedList · Pattern: merge K sorted LL · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Divide and conquer over the `next` chain, like merge sort: split, flatten each half, merge the two sorted `bottom` lists. Disconnect before splitting.
**Coach:** Reusing #22's structure for a k-way merge is creative and gives O(N log k). Your repo code matches the note.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 7 | 5 | 8 | **7.4** |

### #30 · 138. Copy List with Random Pointer
*Sheet: 31-05-2026 · Topic: LinkedList · Pattern: clone a LL · Difficulty H · Status S · 70 min · 4 revisions scheduled*
**Your thinking:** You need a way to map each original node to its copy. A hashmap costs O(n) space. Your own idea (temporarily rewiring pointers) failed, and your notes show why. The working method: put each copy right after its original, set the random pointers, then separate the lists.
**Coach:** Excellent: you recorded the approach that didn't work and why. That kind of exploration is how you get good at new problems.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 7 | 8 | 4 | 8 | **7.6** |

### #58 · 146. LRU Cache
*Sheet: 19-06-2026 · Topic: DLL + Hashing · Pattern: doubly LL + hashing based implementation heavy problem · Difficulty M · Status S · 120 min · 4 revisions scheduled*
**Your thinking:** A doubly linked list ordered by recent use plus a map from key to node. Dummy head and tail remove the edge cases; reuse nodes; erase from the map when you evict. Get and put both move the node to the front.
**Coach:** A thorough design explanation. Your revision note (initialise the dummy links inside the constructor) is the kind of implementation lesson worth keeping. Your claim that reusing nodes avoids "hashmap space complexity" is overstated; the real benefit is fewer allocations.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 7 | 7 | 8 | 3 | 8 | **7.2** |

## Recursion & Backtracking

### #31 · 22. Generate Parentheses
*Sheet: 02-06-2026 · Topic: Recursion & Backtracking · Pattern: generate parenthesis · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Only add "(" while open < n and ")" while close < open; stop when the length is 2n. Bigger lesson: check before you branch rather than generating everything and filtering later.
**Coach:** "Check before you branch" is a principle that carries over to most backtracking. Strong.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 7 | 5 | 8 | **7.8** |

### #32 · Subsequence with Sum K
*Sheet: 03-06-2026 · Topic: Recursion & Backtracking · Pattern: check if subsequence with sum k · Difficulty E · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Return as soon as you find one; the answer is true if picking the element works or skipping it works. Prune when sum > k, which is valid only if all numbers are positive. Always write it as pick / not-pick.
**Coach:** Turning the plain-English logic into a short-circuiting OR is good recursion thinking. Good that you noted when pruning is valid.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 8 | 7 | 6 | 5 | 7 | **6.9** |

### #33 · 78. Subsets
*Sheet: 03-06-2026 · Topic: Recursion & Backtracking · Pattern: generate all subsets · Difficulty E · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** The "recursive leap of faith": trust `solve(i+1)` to generate every subset of the rest, and branch on picking or skipping index i. Record a subset only at the base case.
**Coach:** Clear framing. Your warning against recording early only applies to the pick/skip version; in the loop version (`for j = i..n`) you record at every node, by design. Learn both.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 7 | 6 | 5 | 8 | **7.4** |

### #34 · 90. Subsets II
*Sheet: 03-06-2026 · Topic: Recursion & Backtracking · Pattern: pick and not pick with duplicates · Difficulty M · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** Sort. If you decide not to pick a value, skip all its copies, because picking a later copy would rebuild a subset you already made. Your hand-drawn recursion tree shows this.
**Coach:** Excellent explanation of why the skip works, backed by a drawn tree. This rule ("decide once per group of equal values") comes back in #35, #152 and #158.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 7 | 6 | 4 | 8 | **7.5** |

### #35 · 40. Combination Sum II
*Sheet: 04-06-2026 · Topic: Recursion & Backtracking · Pattern: pick and not pick with duplicates · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** The note only mentions the forgotten prune `if (sum > target) return`.
**Coach:** The main idea is the duplicate skip from #34 (`if (j > i && a[j] == a[j-1]) continue` in the loop version), and it isn't written down. Record the main idea, not just the bug.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 7 | 4 | 4 | 7 | 6 | 5 | 5 | 5 | **5.4** |

### #36 · 131. Palindrome Partitioning
*Sheet: 05-06-2026 · Topic: Recursion & Backtracking · Pattern: pick in an interval · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** From index i, try every end j; only branch when s[i..j] is a palindrome, which cuts out many dead branches.
**Coach:** Good use of the "check before you branch" principle from #31. The upgrade: precompute which substrings are palindromes (O(n²)) so each check is O(1). That links to #143.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 8 | 7 | 6 | 5 | 7 | **6.9** |

### #37 · 79. Word Search
*Sheet: 05-06-2026 · Topic: Recursion & Backtracking · Pattern: dfs · Difficulty M · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** DFS from every cell with a visited array, return as soon as the word is found. Marking a cell '#' in place removes the visited array.
**Coach:** Standard and correct. Add the complexity, O(m·n·3^L), which interviewers expect.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 7 | 7 | 7 | 5 | 4 | 7 | **6.4** |

### #38 · 51. N-Queens
*Sheet: 06-06-2026 · Topic: Recursion & Backtracking · Pattern: backtracking · Difficulty H · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** Track columns and both diagonals with arrays indexed by row + col and col − row + (n − 1). Your notebook also records an approach that failed: marking cells unsafe and then unmarking them breaks when two queens attack the same cell.
**Coach:** Writing down why the marking approach fails shows real understanding (shared marks need counts, not true/false). The diagonal formulas were drawn out, not just memorised. Excellent.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 8 | 7 | 4 | 9 | **7.8** |

### #39 · 139. Word Break
*Sheet: 06-06-2026 · Topic: Recursion & Backtracking + DP · Pattern: basic memoization + hashing · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** The memo marks positions that are dead ends: once every split from index i has failed, never explore i again, because many different paths reach the same i.
**Coach:** A strong explanation of why memoisation helps (the same states are reached repeatedly). Use an unordered_set, or limit split lengths to the longest word.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 7 | 6 | 5 | 8 | **7.5** |

### #40 · 282. Expression Add Operators
*Sheet: 07-06-2026 · Topic: Recursion & Backtracking · Pattern: evaluate mathematical operations in strings using DMAS · Difficulty H · Status S · 120 min · 4 revisions scheduled*
**Your thinking:** Carry the current result and the last number added. For ×, undo that last addition and add `last * cur` instead. Handle leading zeros, use long long, special-case i = 0.
**Coach:** A clean statement of the key trick for operator precedence. 120 minutes (S) shows it was a hard learn; revise it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 9 | 8 | 7 | 8 | 6 | 3 | 7 | **7.0** |

### #41 · 37. Sudoku Solver
*Sheet: 07-06-2026 · Topic: Recursion & Backtracking · Pattern: solve a soduko · Difficulty H · Status H · 50 min · 3 revisions scheduled*
**Your thinking:** Check row, column and box with hash arrays; the box index comes from (i/3, j/3); return as soon as a solution is found.
**Coach:** One inconsistency in your notes: you write the box's top-left corner as `3*(i/3)` (values 0, 3, 6) but size the array `box[4][4][10]`, which would overflow. Index with `i/3, j/3` and use `box[3][3][10]`. Early exit is the right main optimisation.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 7 | 5 | 6 | 6 | 7 | **6.4** |

### #42 · M-Coloring Problem
*Sheet: 07-06-2026 · Topic: Recursion & Backtracking · Pattern: color a graph using atmost M colors · Difficulty M · Status S · 50 min · 4 revisions scheduled*
**Your thinking:** Colour the vertices in order, check neighbours with an isSafe function, and undo the colour on backtrack.
**Coach:** Your quote about undoing the choice ("that path did not work, so undo it") is the core of backtracking. Solid.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 8 | 7 | 7 | 5 | 4 | 7 | **6.6** |

## Stacks, Queues & Monotonic Stack

### #43 · 20. Valid Parentheses
*Sheet: 07-06-2026 · Topic: Stacks & Queues · Pattern: valid parenthesis · Difficulty E · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Use a stack; check it isn't empty before reading the top; at the end the stack must be empty.
**Coach:** Fine. Basic.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 7 | 7 | 6 | 5 | 8 | **6.6** |

### #44 · 155. Min Stack
*Sheet: 07-06-2026 · Topic: Stacks & Queues · Pattern: implement a minStack · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Option 1: store (value, current minimum) pairs. Option 2: one stack where a new minimum is stored as `2*val − min`. The stored value is smaller than the real minimum, which flags it and lets you recover the previous minimum. Use long long.
**Coach:** You explained all three things the encoding has to do (update the minimum, keep the old one, mark the spot). Your revision shows you forgot the long long stack; overflow keeps coming up for you.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 7 | 6 | 8 | 4 | 8 | **7.4** |

### #45 · Next/Previous Greater/Smaller Element templates
*Sheet: 08-06-2026 · Topic: Monotonic Stack · Pattern: implement nge/pge/nse/pse · Difficulty - · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** You keep four templates in your repo. Store indices; pop with >= or <=; NSE and NGE scan from the right, PSE and PGE from the left.
**Coach:** Having one template file is a good habit, and the code is correct. Learn when to use a strict comparison and when not; it matters in #49.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 9 | 8 | 7 | 5 | 8 | **7.4** |

### #46 · 503. Next Greater Element II
*Sheet: 08-06-2026 · Topic: Monotonic Stack · Pattern: find next greater element in a circular array · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Append the array to itself and find the next greater element.
**Coach:** Correct. Looping i from 2n−1 down to 0 with `i % n` avoids the extra copy; use that version.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 6 | 8 | 7 | 6 | 5 | 7 | **6.5** |

### #47 · Number of greater elements to the right
*Sheet: 16-06-2026 · Topic: Sorting · Pattern: find number of greater elements to the right · Difficulty - · Status S · 120 min · 4 revisions scheduled*
**Your thinking:** Merge sort on (value, index) pairs. Every left-half element was originally before every right-half element, so during the merge, when a left element is smaller, all remaining right elements count as greater.
**Coach:** A strong insight, and you build on it in #165. Your repo code handles ties correctly (equal values are not counted). 120 minutes (S), so revise it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 9 | 8 | 9 | 7 | 8 | 3 | 7 | **7.4** |

### #48 · 42. Trapping Rain Water
*Sheet: 16-06-2026 · Topic: Monotonic Stack · Pattern: find total water that would be stored buildings upon rainfall · Difficulty H · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Water above i = min(leftmax, rightmax) − height[i]. You have a prefix-array version, and a two-pointer version where you always move the smaller side, because that side is the limit. Your handwritten correction: the loop is `l <= r`.
**Coach:** The handwritten two-pointer reasoning is correct. Your sheet text says "prefixMin and suffixMin"; that should be **max** arrays. Fix it so revision doesn't plant the wrong word.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 8 | 7 | 9 | 4 | 8 | **7.5** |

### #49 · 907. Sum of Subarray Minimums
*Sheet: 16-06-2026 · Topic: Monotonic Stack · Pattern: sum of all contageous subarray minimums · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Element i contributes arr[i] × (i − pse) × (nse − i). With duplicates, count the leftmost minimum: strict comparison on one side, non-strict on the other.
**Coach:** Your duplicate-handling rule is exactly right and well explained. Watch the long long and modulo arithmetic.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 8 | 5 | 8 | **8.0** |

### #50 · 735. Asteroid Collision
*Sheet: 17-06-2026 · Topic: Monotonic Stack · Pattern: continuous stack operations · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Push to the stack; a collision only happens when the top is positive and the new one negative. A while loop handles the =, < and > size cases.
**Coach:** Clean.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 7 | 7 | 6 | 5 | 7 | **6.8** |

### #51 · 2104. Sum of Subarray Ranges
*Sheet: 17-06-2026 · Topic: Monotonic Stack · Pattern: sum of subarray ranges · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Sum of subarray maximums minus sum of subarray minimums.
**Coach:** Spotting this reduction to #49 is the whole problem. Well done.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 6 | 9 | 7 | 7 | 5 | 8 | **7.1** |

### #52 · 402. Remove K Digits
*Sheet: 17-06-2026 · Topic: Monotonic Stack · Pattern: remove k digits · Difficulty M · Status H · 50 min · 3 revisions scheduled*
**Your thinking:** A greedy increasing stack: remove a digit when the next one is smaller, because the leftmost digits count the most. If k is still left, remove from the end. Strip leading zeros; return "0" if nothing is left.
**Coach:** The greedy reasoning (why removing from the left at a "drop" is best) is well explained. Your revision note says you forgot leading zeros. The sheet link points to your submission, not the problem.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 7 | 6 | 7 | 5 | 7 | **7.0** |

### #53 · 84. Largest Rectangle in Histogram
*Sheet: 17-06-2026 · Topic: Monotonic Stack · Pattern: largest rectangle in histogram · Difficulty H · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** For each bar, width = nse − pse − 1. For one pass: when a bar is popped, the element now on top is its PSE and the current element is its NSE.
**Coach:** Your observation that "anything already in the stack has its PSE known" is the real insight for the one-pass version. Strong.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 7 | 8 | 7 | 8 | 5 | 8 | **7.6** |

### #54 · 85. Maximal Rectangle
*Sheet: 17-06-2026 · Topic: Monotonic Stack · Pattern: implementation of largest rectangle in histogram · Difficulty H · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Turn each row into a histogram and reuse #53.
**Coach:** Good reduction, solved independently.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 6 | 9 | 7 | 7 | 8 | 8 | **7.5** |

### #55 · 239. Sliding Window Maximum
*Sheet: 18-06-2026 · Topic: Monotonic Deque · Pattern: using monotonic dequeue to handle queries · Difficulty H · Status S · 50 min · 4 revisions scheduled*
**Your thinking:** Keep a deque in decreasing order. A new larger element removes smaller ones, because they will leave the window first and are smaller, so they can never be the maximum. The maximum sits at one end. General rule you noted: max/min over a sliding window means a monotonic structure.
**Coach:** The "they can never become the maximum" reasoning and the general rule are excellent. Your choice of which end to push to is unusual; it works, but stick to one standard convention.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 7 | 9 | 7 | 8 | 4 | 8 | **7.6** |

### #56 · 901. Online Stock Span
*Sheet: 18-06-2026 · Topic: Monotonic Stack · Pattern: find pge in a dynamic array · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Previous greater element on a growing array.
**Coach:** Correct reduction; a one-line note is enough here.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 5 | 8 | 7 | 6 | 5 | 7 | **6.4** |

### #142 · 1106. Parsing A Boolean Expression
*Sheet: 06-08-2026 · Topic: Stacks & Queues · Pattern: parse a boolean expression · Difficulty H · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Push characters; at ')' pop back to '(', evaluate, and push the result.
**Coach:** A clean stack evaluator, solved independently.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 7 | 7 | 6 | 8 | 7 | **6.9** |

### #208 · Josephus Problem I (CSES)
*Sheet: 26-10-2026 · Topic: Queues · Pattern: use queue · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Simulate with a queue: move one to the back, remove the next.
**Coach:** Fine for this problem. The note "analyse the pattern" is vague; write the actual queue steps.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 7 | 4 | 4 | 6 | 6 | 5 | 7 | 6 | **5.6** |

## Binary Trees

### #59 · 102. Binary Tree Level Order Traversal
*Sheet: 23-06-2026 · Topic: Binary Trees · Pattern: Level by level traversal · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Take the queue's size at the start of each level and pop exactly that many nodes.
**Coach:** The size snapshot is the key idea, and you explained why it works.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 8 | 8 | 7 | 6 | 4 | 8 | **7.1** |

### #60 · All Traversals (Pre, In, Post), recursive and iterative
*Sheet: 23-06-2026 · Topic: Binary Trees · Pattern: Both recursive + iterative · Difficulty - · Status S · 70 min · 4 revisions scheduled*
**Your thinking:** In a DFS every node is visited three times (before left, between left and right, after right); preorder, inorder and postorder just record different visits. You built a one-stack version with a visit counter, plus iterative inorder and both postorder versions.
**Coach:** The "three visits" model is the deepest way to understand traversals, and your hand-drawn pages show you worked it out. The revision note (forgot it uses a stack) is minor.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 7 | 4 | 8 | **7.8** |

### #61 · 104. Maximum Depth of Binary Tree
*Sheet: 24-06-2026 · Topic: Binary Trees · Pattern: find height of BT · Difficulty E · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Compute left and right heights, return 1 + max. You also clarified that both recursive calls finish before the +1 happens.
**Coach:** You fixed a misunderstanding about evaluation order; that's useful. The height function is your base for #62–#64.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 8 | 6 | 5 | 8 | **7.2** |

### #62 · 110. Balanced Binary Tree
*Sheet: 24-06-2026 · Topic: Binary Trees · Pattern: check if the tree is balanced · Difficulty E · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** A variation of the height function: compute both heights, check the difference, return the height.
**Coach:** Make sure the check happens inside the same height function (return −1 for "unbalanced"); otherwise calling height separately at every node is O(n²). Your note doesn't say which version you use.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 8 | 6 | 5 | 5 | 7 | **6.4** |

### #63 · 543. Diameter of Binary Tree
*Sheet: 24-06-2026 · Topic: Binary Trees · Pattern: find the diameter of a BT · Difficulty E · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** At every node, the longest path through it is left height + right height; track the maximum. Insight: the path between two nodes always goes through their lowest common ancestor, so treat each node as a possible LCA.
**Coach:** The LCA framing is excellent and links trees to paths. Your tree facts (n − 1 edges, unique paths) are correct.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 7 | 7 | 5 | 9 | **7.9** |

### #64 · 124. Binary Tree Maximum Path Sum
*Sheet: 24-06-2026 · Topic: Binary Trees · Pattern: maximum path sum · Difficulty H · Status H · 50 min · 3 revisions scheduled*
**Your thinking:** Return the best downward path from each node; update the answer with left + right + node value; ignore negative branches by clamping them to 0.
**Coach:** A clean extension of #63. You explained why negative branches are dropped.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 7 | 5 | 8 | **7.8** |

### #65 · Tree Boundary Traversal
*Sheet: 25-06-2026 · Topic: Binary Trees · Pattern: tree boundary traversal · Difficulty M · Status H · 50 min · 3 revisions scheduled*
**Your thinking:** Root, then the left boundary (prefer left, otherwise right, skip leaves), then all leaves in order, then the right boundary in reverse. An isLeaf helper avoids duplicates. The root is handled separately so you don't wander onto the right side.
**Coach:** You explained why the root is separate; that's careful edge-case thinking.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 8 | 7 | 7 | 8 | 6 | 5 | 7 | **7.0** |

### #66 · 987. Vertical Order Traversal
*Sheet: 25-06-2026 · Topic: Binary Trees · Pattern: vertical order traversal of BT · Difficulty H · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** Find the column range with a full traversal (not just by walking the outer edges). Shift columns so they start at 0. Store (row, value) per column and sort. Your drawing shows that more than two nodes can share a row and column.
**Coach:** The drawn counterexample shows you test your assumptions, which is a strong habit. A map is simpler; you noted that.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 8 | 7 | 8 | 8 | 7 | 4 | 8 | **7.2** |

### #67 · 101. Symmetric Tree
*Sheet: 25-06-2026 · Topic: Binary Trees · Pattern: check subtrees about root are mirror images of each other · Difficulty E · Status E · 15 min · 1 revisions scheduled*
**Your thinking:** Mirror recursion with NULL checks first.
**Coach:** Fine.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 5 | 7 | 7 | 6 | 8 | 7 | **6.6** |

### #68 · Top/Bottom View of Binary Tree
*Sheet: 25-06-2026 · Topic: Binary Trees · Pattern: top view of BT · Difficulty M · Status H · 25 min · 3 revisions scheduled*
**Your thinking:** Level-order traversal with column numbers. For the top view keep the first node seen in each column; for the bottom view overwrite, so the last one stays.
**Coach:** Good: you got both variations from one change.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 6 | 5 | 8 | **7.2** |

### #69 · 199. Binary Tree Right Side View
*Sheet: 25-06-2026 · Topic: Binary Trees · Pattern: right view of BT · Difficulty M · Status H · 10 min · 3 revisions scheduled*
**Your thinking:** The last node of each level.
**Coach:** A quick reuse of #59.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 5 | 6 | 8 | 7 | 6 | 5 | 8 | **6.8** |

### #70 · 662. Maximum Width of Binary Tree
*Sheet: 26-06-2026 · Topic: Binary Trees · Pattern: max width · Difficulty M · Status H · 60 min · 3 revisions scheduled*
**Your thinking:** Number nodes heap-style (2i+1 / 2i+2, or 2i / 2i+1). On deep trees the numbers overflow, so on each level subtract the leftmost index; gaps stay the same and numbers stay small. Your diagram shows it level by level.
**Coach:** An excellent explanation of why normalising works ("shifting everything by a constant keeps the differences"). The INT_MAX initialisation bug was a good catch.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 8 | 7 | 5 | 9 | **7.9** |

### #71 · 236. Lowest Common Ancestor of a Binary Tree
*Sheet: 27-06-2026 · Topic: Binary Trees · Pattern: LCA · Difficulty M · Status S · 50 min · 4 revisions scheduled*
**Your thinking:** Each call answers: does this subtree contain p, q or their LCA? Return the node if it's p or q; if both sides return something, this node is the LCA; otherwise pass up whichever side is not NULL.
**Coach:** One of your best explanations: you define what the function returns before writing it. Use that approach for every tree recursion.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 9 | 9 | 8 | 7 | 4 | 9 | **8.1** |

### #72 · Children Sum in a Binary Tree
*Sheet: 27-06-2026 · Topic: Binary Trees · Pattern: children sum property · Difficulty M · Status H · 15 min · 3 revisions scheduled*
**Your thinking:** Recursively check the sum at each non-leaf node and AND the results.
**Coach:** Fine.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 7 | 7 | 6 | 5 | 7 | **6.5** |

### #73 · 863. All Nodes Distance K in Binary Tree
*Sheet: 27-06-2026 · Topic: Binary Trees · Pattern: traversing up the binary tree · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Map each node to its parent so you can also move upward, then BFS or DFS from the target with a visited set.
**Coach:** Turning the tree into a graph with parent links is a very reusable idea.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 6 | 5 | 8 | **7.2** |

### #74 · 222. Count Complete Tree Nodes
*Sheet: 27-06-2026 · Topic: Binary Trees · Pattern: count no. of Nodes in complete BT in Log(2N) time · Difficulty E · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** If the leftmost and rightmost heights are equal, the subtree is perfect and has 2^h − 1 nodes; otherwise recurse. That gives O(log² n). You derived the geometric series.
**Coach:** Excellent: you proved the formula and the complexity.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 7 | 7 | 9 | 5 | 8 | **7.8** |

### #75 · 105. Construct Binary Tree from Preorder and Inorder Traversal
*Sheet: 28-06-2026 · Topic: Binary Trees · Pattern: construct BT from inorder and preorder traversal · Difficulty M · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** The first preorder element is the root; find it in inorder to split left and right; the size of the left part tells you how to split preorder. A hashmap makes each lookup O(1), so the whole thing is O(n) instead of O(n²).
**Coach:** A full derivation, including the optimisation. Strong.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 9 | 4 | 8 | **8.0** |

### #76 · 106. Construct Binary Tree from Inorder and Postorder Traversal
*Sheet: 28-06-2026 · Topic: Binary Trees · Pattern: construct BT from inorder and postorder traversal · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Same as #75, but the root is the last postorder element.
**Coach:** Good transfer. Remember to build the right subtree first when you read postorder from the end.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 5 | 9 | 7 | 7 | 5 | 8 | **7.0** |

### #77 · 114. Flatten Binary Tree to Linked List
*Sheet: 28-06-2026 · Topic: Binary Trees + LL · Pattern: flatten a BT to LL · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Preorder traversal attaching each node to a dummy tail; save left and right before detaching.
**Coach:** Correct, but it uses O(h) space. The O(1)-space follow-up uses the Morris idea from #79 (link the rightmost node of the left subtree to the right subtree). You know Morris, so connect them.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 6 | 7 | 5 | 5 | 7 | **6.2** |

### #78 · 297. Serialize and Deserialize Binary Tree
*Sheet: 28-06-2026 · Topic: Binary Trees · Pattern: serialize and deserialize a BT · Difficulty H · Status H · 60 min · 3 revisions scheduled*
**Your thinking:** Level-order with '#' for nulls; use to_string and stoi.
**Coach:** Works. Write the format explicitly (delimiter, how many null markers) so you can reproduce it under pressure.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 5 | 7 | 6 | 6 | 5 | 7 | **6.1** |

### #79 · 94. Binary Tree Inorder Traversal (Morris)
*Sheet: 29-06-2026 · Topic: Binary Trees · Pattern: Morris Inorder Traversal of BT · Difficulty M · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** Temporary links from each node's in-order predecessor back to the node let you return without a stack. The first visit creates the link and goes left; the second removes it, visits and goes right. Don't forget the `pred->right != curr` check. For preorder, visit when you create the link.
**Coach:** A deep explanation, including how many times each node is visited. Excellent.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 9 | 9 | 9 | 9 | 4 | 9 | **8.5** |

### #118 · 337. House Robber III
*Sheet: 21-07-2026 · Topic: Tree DP · Pattern: dp on trees · Difficulty M · Status S · 30 min · 4 revisions scheduled*
**Your thinking:** Postorder DP with pick and not-pick states at each node: pick the node and skip its children, or skip it and take the best of each child.
**Coach:** Right state design. Return a pair {rob, skip} from each call instead of using two maps; that's O(1) extra per node and cleaner.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 6 | 4 | 8 | **7.1** |

*#201 is under Binary Search.*

## Binary Search Trees

### #80 · Floor and Ceil in a BST
*Sheet: 29-06-2026 · Topic: Binary Search Trees · Pattern: floor and ceil in bst · Difficulty E · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Walk down the tree like a binary search, keeping the best candidate so far.
**Coach:** Correct. One error in your notes: you define "balanced" as "all levels except the last are full", which is the definition of a *complete* tree. Balanced means height O(log n) (AVL: subtree heights differ by at most 1). Fix this; it's an interview red flag.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 8 | 7 | 7 | 8 | 7 | **7.1** |

### #81 · 450. Delete Node in a BST
*Sheet: 29-06-2026 · Topic: Binary Search Trees · Pattern: delete a node in BST · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** `root->left = delete(root->left, key)`: treat every node as a possible parent that relinks to whatever is returned. A node with zero or one child returns its other child; with two children, copy the in-order successor's value and delete the successor from the right subtree.
**Coach:** You turned this into a general pattern for changing trees (insert, delete, prune). That's real abstraction.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 9 | 10 | 8 | 8 | 4 | 9 | **8.4** |

### #82 · 701. Insert into a Binary Search Tree
*Sheet: 29-06-2026 · Topic: Binary Search Trees · Pattern: insert a node in BST · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Iterative O(1) space; also learned the recursive "relink" version.
**Coach:** Your revision note says you forgot to break after inserting. Small but typical.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 6 | 7 | 5 | 8 | **7.2** |

### #83 · 230. Kth Smallest Element in a BST
*Sheet: 30-06-2026 · Topic: Binary Search Trees · Pattern: find k-th smallest element in bst · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** The k-th inorder element. Use a stack, or Morris, but with Morris you can't exit early because a temporary link might still be there; finish the traversal.
**Coach:** The Morris early-exit catch is advanced; most people miss it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 9 | 8 | 5 | 8 | **8.1** |

### #84 · 235. LCA of a Binary Search Tree
*Sheet: 30-06-2026 · Topic: Binary Search Trees · Pattern: find the LCA in logN time · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Use the BST ordering: the LCA is the first node with value between min(p, q) and max(p, q), inclusive, because p or q can itself be the LCA.
**Coach:** You explained why the bounds are inclusive. Good. Note the time is O(h), which is O(log n) only for balanced trees.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 7 | 5 | 8 | **7.6** |

### #85 · 1008. Construct BST from Preorder Traversal
*Sheet: 01-07-2026 · Topic: Binary Search Trees · Pattern: construct BST from preorder traversal · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** The root is the first element; binary search for where values become larger to split the left and right parts; recurse.
**Coach:** That's O(n log n). The O(n) optimum passes an upper bound down the recursion and uses one shared index; this is the same bounds idea as your #88. Learn it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 8 | 7 | 5 | 5 | 7 | **6.8** |

### #86 · Predecessor and Successor
*Sheet: 01-07-2026 · Topic: Binary Search Trees · Pattern: find inorder successor and predecessor of a key in BST · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Two walks down the tree keeping the best candidates, like binary search.
**Coach:** Clean.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 7 | 7 | 8 | 8 | **7.6** |

### #87 · Merge two BSTs
*Sheet: 01-07-2026 · Topic: Binary Search Trees · Pattern: merge two BSTs, construct a BST from inorder traversal · Difficulty - · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Inorder both trees, merge the sorted lists, build a balanced BST from the middle out. All O(N + M).
**Coach:** Correct and your repo code is clean. The follow-up interviewers ask: produce the merged inorder with two iterators (stacks) in O(h1 + h2) space.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 8 | 7 | 8 | 5 | 7 | **7.1** |

### #88 · 98. Validate Binary Search Tree
*Sheet: 01-07-2026 · Topic: Binary Search Trees · Pattern: check if a BST is valid or not · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Either the inorder must be strictly increasing, or pass (min, max) bounds down the tree, using long long for the bounds. You also discussed whether this is top-down or bottom-up.
**Coach:** The top-down vs bottom-up discussion shows you think about how information flows. Strong.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 7 | 5 | 8 | **7.9** |

### #89 · 1373. Maximum Sum BST in Binary Tree
*Sheet: 02-07-2026 · Topic: Binary Search Trees · Pattern: largest BST in binary tree · Difficulty H · Status S · 90 min · 4 revisions scheduled*
**Your thinking:** Postorder, returning {max, min, isBST, sum} for each subtree. NULL returns {INT_MIN, INT_MAX, true, 0} so leaves work automatically. You also argued why min and max being wrong inside non-BST subtrees doesn't matter.
**Coach:** That correctness argument is excellent. This is bottom-up DP on a tree, done well.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 8 | 9 | 9 | 8 | 3 | 9 | **8.1** |

### #90 · 99. Recover Binary Search Tree
*Sheet: 03-07-2026 · Topic: Binary Search Trees · Pattern: swap two nodes to regain BST property · Difficulty M · Status H · 60 min · 3 revisions scheduled*
**Your thinking:** In the inorder sequence, a swap creates either two "drops" (non-adjacent swap) or one (adjacent swap). Rule: at the first drop record both elements; at a second drop update the second one. Morris gives O(1) space.
**Coach:** Your doc builds the reasoning from first principles. The adjacent-swap case is handled properly.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 9 | 8 | 9 | 8 | 4 | 9 | **8.2** |

### #91 · 653. Two Sum IV - Input is a BST
*Sheet: 03-07-2026 · Topic: Binary Search Trees · Pattern: check if two nodes exist in BST such that their sum is K · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Brute force: inorder list plus two pointers, O(n) space. Optimal: two BST iterators (forward and reverse stacks), O(h) space, linked to the BST Iterator problem.
**Coach:** A good space-optimisation step and good transfer.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 9 | 7 | 8 | 4 | 8 | **7.5** |

### #92 · 1932. Merge BSTs to Create Single BST
*Sheet: 03-07-2026 · Topic: Binary Search Trees · Pattern: merge n BSTs to make a valid BST · Difficulty H · Status S · 120 min · 4 revisions scheduled*
**Your thinking:** The global root must be a root value that never appears as a leaf. Attach the other trees at matching leaves, check all were used, then validate the BST. Your doc argues that if a BST is possible the shape is unique, and that cycles or several candidate roots make it impossible.
**Coach:** Careful uniqueness reasoning on a hard problem (120 min, S). Your doc mentions "just ask Gemini" about erasing from the map; that's fine for learning, but practise defending such choices yourself.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 9 | 7 | 7 | 8 | 7 | 3 | 7 | **7.0** |

## Graphs

### #93 · Undirected Graph Cycle
*Sheet: 03-07-2026 · Topic: Graphs · Pattern: detect cycle in undirected graph using BFS and DFS · Difficulty E · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Finding an already-visited node means a cycle unless it's the parent; check every connected component. You wrote both BFS and DFS versions.
**Coach:** Correct, and your repo code matches. One edge case: the parent check fails with two parallel edges between the same pair (then you track the edge id instead).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 7 | 7 | 8 | 8 | **7.6** |

### #94 · Directed Graph Cycle
*Sheet: 04-07-2026 · Topic: Graphs · Pattern: detect cycle in directed graph using BFS and DFS · Difficulty E · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** DFS with visited plus "on current path" arrays; or Kahn's algorithm (a cycle exists if fewer than V nodes get processed).
**Coach:** The sheet note is just a link, but your repo code and #97 show you understand it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 5 | 9 | 7 | 7 | 8 | 8 | **7.4** |

### #95 · 127. Word Ladder
*Sheet: 04-07-2026 · Topic: Graphs · Pattern: word ladder · Difficulty H · Status E · 40 min · 1 revisions scheduled*
**Your thinking:** Reframe the question as shortest paths from the start word to every word, using BFS; erase a word from the set once visited, because the first time BFS reaches it is the shortest.
**Coach:** You explained why erasing on first visit is correct. Add the complexity: O(N · L · 26).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 7 | 6 | 8 | 8 | **7.8** |

### #96 · 126. Word Ladder II
*Sheet: 05-07-2026 · Topic: Graphs · Pattern: word ladder 2 · Difficulty H · Status H · 120 min · 3 revisions scheduled*
**Your thinking:** Version 1: keep whole paths in the queue, only extending when dist[child] = dist[parent] + 1. Version 2: BFS builds a graph of shortest paths, then DFS pulls out the paths. That still timed out, so Version 3 builds the graph backwards and runs DFS from the end word, so every branch is useful.
**Coach:** Three versions, each fixing the previous one's bottleneck. This is a model of how to optimise.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 9 | 3 | 8 | **7.9** |

### #97 · Topological Sorting
*Sheet: 05-07-2026 · Topic: Graphs · Pattern: topo sort · Difficulty - · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** DFS topological sort uses finish order and assumes there's no cycle. Kahn's processes nodes once their in-degree hits 0 and finds a cycle when the output has fewer than V nodes. DFS orders by outgoing edges finished; Kahn's by incoming edges cleared.
**Coach:** The contrast between the two is well put.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 7 | 8 | 9 | **8.4** |

### #98 · 802. Find Eventual Safe States
*Sheet: 06-07-2026 · Topic: Graphs · Pattern: reverse graph + kahn's algorithm / direct DFS · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Reverse the graph and run Kahn's; whatever never reaches in-degree 0 is on a cycle or leads into one. Alternatively, DFS: whatever stays on the path array is unsafe. You argued why restarting the DFS from new starting points still covers everything.
**Coach:** Two methods, a proof sketch and a diagram. Your revision note captures the difference between the forward and reversed versions.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 7 | 5 | 8 | **7.9** |

### #99 · Alien Dictionary
*Sheet: 06-07-2026 · Topic: Graphs · Pattern: construct an custom adj list + topo sort to check · Difficulty H · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Compare neighbouring words at their first differing letter to add an edge; if one word is a prefix of the next but longer, the order is invalid; record every letter used; then Kahn's.
**Coach:** You handled the prefix-invalid case and the single-word case, both common misses.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 9 | 8 | 7 | 5 | 8 | **7.6** |

### #100 · Shortest Paths (overview)
*Sheet: 06-07-2026 · Topic: Graphs · Pattern: all shortest paths algos combined · Difficulty - · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** A decision guide: unit weights use BFS; a DAG uses topological order (works with negative weights); non-negative weights use Dijkstra; negative weights use Bellman-Ford; all pairs use Floyd-Warshall.
**Coach:** A strong overview. One correction: in an **undirected** graph a negative edge becomes two directed edges, which form a negative cycle immediately. Bellman-Ford will always report a cycle; "use Bellman-Ford for negative weights in undirected graphs" is misleading. Your Dijkstra doc ("maybe vs never") is excellent. Your repo's Dijkstra comments are out of date: they say the priority queue holds negative distances, but your code uses a min-heap. They also say negative weights cause an infinite loop, which is only true with negative *cycles*; otherwise you get wrong answers or exponential time.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 10 | 7 | 9 | 8 | 8 | **8.5** |

### #101 · 1631. Path With Minimum Effort
*Sheet: 07-07-2026 · Topic: Graphs · Pattern: find path with minimum effort · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Dijkstra where a path's cost is its largest single step.
**Coach:** Spotting the "minimise the maximum" variant is the key. The same problem can also be solved with binary search plus BFS, or with DSU (see #111).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 6 | 8 | 7 | 6 | 8 | 7 | **7.1** |

### #102 · 787. Cheapest Flights Within K Stops
*Sheet: 08-07-2026 · Topic: Graphs · Pattern: find shortest path with atmost K + 1 edges · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Dijkstra loses track of how many edges a path used, so use Bellman-Ford for K+1 rounds, reading from the old array and writing to a copy so one round can't chain several edges. Or BFS by number of stops, storing the cost in the queue (your $50/$150 example shows why). You also derived Bellman-Ford as a DP over "at most k edges" and Floyd-Warshall's k-outermost loop.
**Coach:** Your best graph write-up: the copy-array explanation and the counterexample are what interviewers look for.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 9 | 9 | 8 | 8 | 5 | 9 | **8.4** |

### #103 · 1976. Number of Ways to Arrive at Destination
*Sheet: 08-07-2026 · Topic: Graphs · Pattern: count the number of shortest paths in dijkstra · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** In Dijkstra, a strictly shorter path replaces the way-count; an equal one adds to it. Big lesson about stale entries: skip a popped entry when its distance is larger than the recorded best, or use the popped distance in the comparison.
**Coach:** Your stale-entry analysis applies to every Dijkstra you'll write. Don't forget the modulo.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 7 | 5 | 9 | **8.0** |

### #104 · Minimum Multiplications to reach End
*Sheet: 08-07-2026 · Topic: Graphs · Pattern: minimum multiplications to get to a target · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Every edge has weight 1, so plain BFS over the values 0 to 99999 (mod 1e5) is enough.
**Coach:** Choosing BFS over Dijkstra is the right call.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 7 | 7 | 8 | 8 | **7.6** |

### #105 · Minimum Spanning Tree (Prim, Kruskal)
*Sheet: 15-07-2026 · Topic: Graphs · Pattern: minimum spanning trees · Difficulty - · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Prim: grow from a node, always taking the smallest edge to an unvisited node (lazy priority queue), O(E log E). Kruskal: sort edges and add them with DSU when they join different components.
**Coach:** Code is correct; Prim's comment about the visited check saving memory is good. Missing: *why* the greedy is correct (the cut property). Write one line on it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 7 | 8 | 7 | 8 | 8 | 7 | **7.5** |

### #106 · 1319. Number of Operations to Make Network Connected
*Sheet: 16-07-2026 · Topic: Graphs · Pattern: Disjoint Set · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** No notes.
**Coach:** I can't judge this one: the Insight column is empty. The key fact: if edges < n − 1 the answer is −1, otherwise it's (number of components − 1). Add a note.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 3 | 2 | 7 | 6 | 5 | 8 | 4 | **5.4** |

### #107 · 947. Most Stones Removed with Same Row or Column
*Sheet: 16-07-2026 · Topic: Graphs · Pattern: Disjoint Set · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Stones sharing a row or column are connected; join all pairs (O(N²), fine for N = 1000). A greedy row/column marking fails because it depends on the order.
**Coach:** You were right that greedy fails. But your note says "only brute force works", which isn't true. The O(N) solution treats each row r and each column (c + offset) as DSU nodes and joins them per stone; answer = stones − components. Learn this "rows and columns as nodes" trick; it's common.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 7 | 6 | 6 | 6 | 6 | 4 | 5 | 6 | **5.8** |

### #108 · 721. Accounts Merge
*Sheet: 16-07-2026 · Topic: Graphs · Pattern: Disjoint Set · Difficulty M · Status H · 60 min · 3 revisions scheduled*
**Your thinking:** Use a DSU over account indices; map each email to the first account that had it; join accounts sharing an email; then group emails by root in a sorted map.
**Coach:** Clear, with complexity. You explained why any account can represent the group.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 8 | 7 | 8 | 5 | 8 | **7.5** |

### #109 · Number of Islands II (online)
*Sheet: 17-07-2026 · Topic: Graphs · Pattern: Disjoint Set · Difficulty M · Status S · 60 min · 4 revisions scheduled*
**Your thinking:** Each new land cell starts as a separate island (count++); join it with neighbouring land cells that have a different root (count−− each time); land that's already there leaves the count unchanged. Encode cells as i·m + j.
**Coach:** The "assume isolated, then test" framing is very clear. 60 min (S); revise it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 7 | 4 | 8 | **7.6** |

### #110 · 827. Making A Large Island
*Sheet: 17-07-2026 · Topic: Graphs · Pattern: Disjoint Set · Difficulty H · Status H · ? min · 3 revisions scheduled*
**Your thinking:** Union by size to build islands; for each water cell, add up the sizes of the distinct neighbouring roots (a set removes duplicates) plus one; handle the all-land case.
**Coach:** Good, including the all-ones edge case. The time taken isn't recorded.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 9 | 8 | 7 | 5 | 8 | **7.6** |

### #111 · 778. Swim in Rising Water
*Sheet: 17-07-2026 · Topic: Graphs · Pattern: Binary Search + DFS · Difficulty H · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Binary search on the time, checking reachability with DFS.
**Coach:** Valid, O(n² log n). Dijkstra on the largest value along the path, or DSU adding cells in order of height, are the standard alternatives; connect this to #101.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 7 | 7 | 6 | 8 | 7 | **6.9** |

### #112 · Strongly Connected Components (Kosaraju, Tarjan)
*Sheet: 19-07-2026 · Topic: Graphs · Pattern: SCC · Difficulty - · Status E · 60 min · 1 revisions scheduled*
**Your thinking:** Kosaraju: order nodes by DFS finish time, reverse the graph, DFS in that order, and each tree is an SCC (shrinking each SCC to one node gives a DAG). Tarjan: discovery time and low-link values; use disc[v], not low[v], on edges back into the current stack; ignore nodes whose SCC is already finished; pop when low == disc.
**Coach:** Your Tarjan doc explains exactly why disc[v] is used rather than low[v], the subtlest line. Excellent.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 9 | 9 | 8 | 8 | 8 | 9 | **8.8** |

### #113 · Bridges in a graph (1192. Critical Connections)
*Sheet: 19-07-2026 · Topic: Graphs · Pattern: SCC · Difficulty H · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Undirected Tarjan: no stack needed; track the parent; edge u–v is a bridge if low[v] > disc[u]. Your whiteboard shows the result doesn't depend on DFS order.
**Coach:** Checking that the result doesn't depend on DFS order is a good test of understanding. Note: pass `time` by reference.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 8 | 5 | 9 | **8.1** |

### #114 · Articulation Points
*Sheet: 19-07-2026 · Topic: Graphs · Pattern: SCC · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** A non-root node u is an AP if a child v has low[v] >= disc[u]; the root is an AP only if it has more than one DFS child. Your whiteboard covers the <, = and > cases.
**Coach:** Your revision says you forgot the `par == -1` check and passing the parent. Lock it in with the side-by-side: bridge uses `>`, articulation point uses `>=` plus the root rule.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 6 | 8 | 5 | 8 | **7.8** |

## Greedy

### #115 · 2498. Frog Jump II
*Sheet: 21-07-2026 · Topic: Greedy · Pattern: Greedy · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Use every other stone going and the remaining ones coming back, so the answer is max(stones[i+2] − stones[i]).
**Coach:** Correct greedy, but the note doesn't really prove it. Practise a short exchange argument.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 6 | 7 | 6 | 5 | 7 | **6.4** |

### #168 · 55. Jump Game
*Sheet: 08-09-2026 · Topic: Greedy · Pattern: increase window size gradually · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Track the farthest reachable index; fail if i goes beyond it.
**Coach:** Clean.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 7 | 5 | 8 | **7.6** |

### #169 · 45. Jump Game II
*Sheet: 09-09-2026 · Topic: Greedy · Pattern: find minimum jumps to reach end · Difficulty M · Status S · 50 min · 4 revisions scheduled*
**Your thinking:** Treat it like BFS levels: within the current window find the farthest reach; when you reach the window's end, jump++ and the next window ends at that farthest point. Stop at n − 2.
**Coach:** Seeing it as BFS levels is the right model, and the n − 2 detail is the classic trap.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 8 | 4 | 8 | **7.8** |

### #170 · 678. Valid Parenthesis String
*Sheet: 09-09-2026 · Topic: Greedy · Pattern: check if string is a valid parenthesis · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Track the minimum and maximum number of unmatched '(' at once (treating '*' as ')' or '('). Fail if the maximum goes below 0; clamp the minimum at 0; succeed if the minimum ends at 0.
**Coach:** A beautiful explanation: tracking a range instead of branching. You reused it in #194.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 8 | 9 | 9 | 8 | 4 | 9 | **8.2** |

### #171 · 135. Candy
*Sheet: 10-09-2026 · Topic: Greedy · Pattern: decompose complicated logic into two simple greedy passes · Difficulty H · Status S · 30 min · 4 revisions scheduled*
**Your thinking:** Two passes: left to right for the left neighbour rule, right to left for the right one, combined with max. Takeaway: when each element depends on both neighbours, handle each side separately and then merge.
**Coach:** Your takeaway generalises well. Excellent.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 9 | 10 | 8 | 8 | 4 | 9 | **8.2** |

### #172 · Minimum Platforms
*Sheet: 10-09-2026 · Topic: Greedy · Pattern: break the problem intuitively and don't fall into the trap of thinking by traditional logic · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Stop tracking individual trains; think like the station master who only counts how many are present. Sort arrivals and departures separately; for each arrival count departures before it with binary search.
**Coach:** The change of viewpoint is the real lesson. The standard version is a two-pointer sweep over both sorted arrays, O(n log n) for the sort and O(n) after. Your binary search version works too.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 7 | 7 | 5 | 8 | **7.5** |

### #173 · Job Sequencing Problem
*Sheet: 12-09-2026 · Topic: Greedy · Pattern: sequence jobs to maximize profit · Difficulty M · Status H · 50 min · 3 revisions scheduled*
**Your thinking:** Sort by profit descending; place each job in the latest free slot before its deadline. DSU makes "find the latest free slot" near O(1).
**Coach:** Using DSU for "next free slot" is advanced and reusable.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 9 | 7 | 9 | 5 | 8 | **7.8** |

### #174 · 57. Insert Interval
*Sheet: 12-09-2026 · Topic: Greedy · Pattern: same as merge intervals · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Add the new interval, sort, run merge intervals.
**Coach:** Works, but the input is already sorted, so sorting throws away the O(n) solution: copy everything before the new interval, merge the overlapping ones, copy the rest. Interviewers want the O(n) version.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 7 | 5 | 5 | 7 | 6 | 4 | 8 | 6 | **6.0** |

### #175 · 435. Non-overlapping Intervals
*Sheet: 12-09-2026 · Topic: Greedy · Pattern: remove min intervals to make others non overlapping · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Sort by end time and keep intervals that finish earliest. Rule: to maximise count or minimise deletions, sort by end; to merge or group, sort by start.
**Coach:** That rule is a great summary of interval greedy.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 10 | 7 | 7 | 5 | 9 | **7.9** |

### #204 · 846. Hand of Straights
*Sheet: 18-10-2026 · Topic: Greedy · Pattern: create bundles of consecutive numbers · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Sort and count; each smallest value still remaining must start a group; fail if a group can't be completed.
**Coach:** Correct, solved independently.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 7 | 6 | 8 | 8 | **7.5** |

## Dynamic Programming

### #116 · 198. House Robber
*Sheet: 21-07-2026 · Topic: DP · Pattern: max sum of non adjacent elements · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** dp[i] = best from the first i houses = max(rob house i + dp[i−2], dp[i−1]). You also wrote an explicit two-state version (dp[i][0/1]) as practice for harder problems.
**Coach:** Practising explicit state design on an easy problem is a smart habit.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 7 | 5 | 8 | **7.8** |

### #117 · 213. House Robber II
*Sheet: 21-07-2026 · Topic: DP · Pattern: max sum of non adjacent circular elements · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** The first and last house can't both be robbed. Two DP arrays: one with house 1 removed, one normal; combine "last house robbed" from the first with "last house not robbed" from the second.
**Coach:** Your combination is correct but harder to explain than the standard answer: max(rob(0..n−2), rob(1..n−1)). Use the standard one in interviews.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 5 | 8 | 7 | 6 | 5 | 7 | **6.6** |

### #119 · 1463. Cherry Pickup II
*Sheet: 22-07-2026 · Topic: DP · Pattern: handling multiple states in grid · Difficulty H · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** State dp[x1][x2][row]: both robots move down together; add both cells, counting once if they're on the same cell; try all 9 move pairs.
**Coach:** The key step is noticing both robots are always on the same row, so you need a three-index state. Solved independently (E). Strong.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 9 | 8 | 7 | 8 | 8 | **8.0** |

### #120 · 494. Target Sum
*Sheet: 28-07-2026 · Topic: DP · Pattern: number of ways to form a particular sum (using offset) · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Every reachable sum is in [−S, S]; shift by S so indices are non-negative; dp[i][j] = dp[i−1][j − a] + dp[i−1][j + a]; return 0 if the target is out of range.
**Coach:** The shift works. The neater version: count subsets with sum (S + target)/2, return 0 if S + target is odd. Connect it to #124.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 8 | 7 | 7 | 7 | 6 | 8 | 7 | **7.2** |

### #121 · 416. Partition Equal Subset Sum
*Sheet: 28-07-2026 · Topic: DP · Pattern: 0/1 knapsack problem · Difficulty M · Status E · 40 min · 1 revisions scheduled*
**Your thinking:** dp[i][j]: can the first i elements make sum j.
**Coach:** One line. Add: the total must be even, the target is total/2, and the 1D version loops j backwards.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 4 | 4 | 7 | 6 | 5 | 8 | 6 | **6.0** |

### #122 · 2035. Partition Array Into Two Arrays to Minimize Sum Difference
*Sheet: 29-07-2026 · Topic: DP · Pattern: meet in the middle · Difficulty H · Status H · 50 min · 3 revisions scheduled*
**Your thinking:** Meet in the middle: list subset sums of each half grouped by size; for each left sum, binary search the matching size on the right for the value closest to total/2. Your doc proves why checking only "≤ target" is enough (each subset's complement is equally far on the other side).
**Coach:** The complement argument is a genuine proof. Excellent for a hard problem.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 8 | 9 | 5 | 8 | **8.0** |

### #123 · Count Subsets with Sum K
*Sheet: 30-07-2026 · Topic: DP · Pattern: 0/1 knapsack problem · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Pick / not-pick counting DP up to the target.
**Coach:** The GFG version has zeros in the input. Your dp must start j at 0 (each zero doubles the count). Note this.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 5 | 8 | 6 | 6 | 8 | 6 | **6.5** |

### #124 · Partitions with Given Difference
*Sheet: 30-07-2026 · Topic: DP · Pattern: 0/1 knapsack problem · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Same as subset counting; don't just compute (sum − diff)/2, since the division can lose an odd remainder. You search for i with sum − 2i == diff instead.
**Coach:** You found the parity trap. A direct check (`(sum − diff) % 2 == 0` and sum ≥ diff) is simpler.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 8 | 8 | 6 | 8 | 7 | **7.4** |

### #125 · 322. Coin Change
*Sheet: 30-07-2026 · Topic: DP · Pattern: unbounded knapsack · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** dp[i][j] = fewest coins using the first i types to make j. Taking coin i stays in row i (`dp[i][j − c]`) because you can reuse it.
**Coach:** You explained why it's dp[i] and not dp[i−1], which is the core of unbounded knapsack.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 7 | 8 | 8 | **8.1** |

### #126 · Coin Combinations II (CSES)
*Sheet: 30-07-2026 · Topic: DP · Pattern: unbounded knapsack · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Count combinations: dp[i][j] = dp[i−1][j] + dp[i][j−c]. Space optimise to two rows. Distinct combinations are guaranteed because once you stop using a coin you never use it again.
**Coach:** The "once you stop, never again" ordering explanation is the important bit.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 7 | 8 | 5 | 8 | **7.8** |

### #127 · Rod Cutting
*Sheet: 30-07-2026 · Topic: DP · Pattern: unbounded knapsack · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Unbounded knapsack where piece length i sells for price[i−1]. You realised "cut" really means "allowed piece size".
**Coach:** Rewording the problem to remove the confusion is a good skill.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 8 | 9 | 7 | 7 | 5 | 8 | **7.5** |

### #128 · Print Longest Common Subsequence
*Sheet: 30-07-2026 · Topic: DP · Pattern: LCS · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Standard LCS on prefixes with 1-based indexing, then walk back from dp[n][m].
**Coach:** Clean.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 7 | 8 | 8 | **8.1** |

### #129 · 1312. Minimum Insertion Steps to Make a String Palindrome
*Sheet: 31-07-2026 · Topic: DP · Pattern: LCS · Difficulty H · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Answer = n − LPS. Your explanation talks about inserting characters where two strings differ.
**Coach:** The answer is right, but the explanation is confused. Correct reasoning: every character not in the longest palindromic subsequence needs one mirrored copy inserted, so n − LPS, and LPS = LCS(s, reverse(s)). Rewrite it so you can defend it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 4 | 4 | 8 | 7 | 7 | 8 | 6 | **6.5** |

### #130 · 1092. Shortest Common Supersequence
*Sheet: 31-07-2026 · Topic: DP · Pattern: LCS · Difficulty H · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Walk back through the LCS table, adding every character, with shared ones once.
**Coach:** Good reuse of #128.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 6 | 9 | 7 | 7 | 8 | 8 | **7.6** |

### #131 · 115. Distinct Subsequences
*Sheet: 31-07-2026 · Topic: DP · Pattern: LCS · Difficulty H · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** dp[i][j] = dp[i−1][j] + (s[i] == t[j] ? dp[i−1][j−1] : 0); dp[i][0] = 1. Big values overflow, but since the final answer fits in 32 bits, the intermediate overflow can be absorbed with unsigned.
**Coach:** The overflow reasoning is insightful. Write the base cases, as you did.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 8 | 7 | 5 | 8 | **7.8** |

### #132 · 44. Wildcard Matching
*Sheet: 31-07-2026 · Topic: DP · Pattern: LCS · Difficulty H · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Prefix DP: '?' or a match takes dp[i−1][j−1]; '*' takes dp[i−1][j] (uses a character) OR dp[i][j−1] (matches nothing); careful base case for leading '*'.
**Coach:** You explained both choices for '*' clearly.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 7 | 5 | 8 | **7.8** |

### #133 · 188. Best Time to Buy and Sell Stock IV
*Sheet: 01-08-2026 · Topic: DP · Pattern: Dp on stocks · Difficulty H · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** One framework for all stock problems: dp[day][transactions][canBuy], filled from the end; base cases are day n or k transactions done.
**Coach:** A general framework that covers the whole family; #134 and #135 show it works.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 10 | 8 | 7 | 5 | 9 | **8.0** |

### #134 · 714. Best Time to Buy and Sell Stock with Transaction Fee
*Sheet: 01-08-2026 · Topic: DP · Pattern: Dp on stocks · Difficulty M · Status H · 10 min · 3 revisions scheduled*
**Your thinking:** Same framework; subtract the fee when selling.
**Coach:** Quick transfer.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 5 | 9 | 7 | 7 | 5 | 8 | **7.0** |

### #135 · 122. Best Time to Buy and Sell Stock II
*Sheet: 01-08-2026 · Topic: DP · Pattern: Dp on stocks · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** "Just try the DP approach."
**Coach:** Also learn the greedy answer (add up every positive day-to-day difference) and why it's equivalent.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 4 | 3 | 8 | 7 | 5 | 8 | 6 | **6.1** |

### #136 · 368. Largest Divisible Subset
*Sheet: 02-08-2026 · Topic: DP · Pattern: LIS using sort · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Sorting doesn't change the answer's size and makes divisibility one-directional; then LIS with `a[i] % a[j] == 0`, plus a parent array to rebuild the subset.
**Coach:** You justified why sorting is allowed.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 7 | 7 | 5 | 8 | **7.6** |

### #137 · 1048. Longest String Chain
*Sheet: 02-08-2026 · Topic: DP · Pattern: LIS using custom sort · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Sort by length; LIS with an O(L) "is it the predecessor" check using a single pointer. Comparators must be strict (`<`, not `<=`).
**Coach:** The strict comparator lesson is valuable C++ knowledge. Faster alternative: a hashmap from word to its best chain, deleting one letter at a time.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 7 | 5 | 8 | **7.6** |

### #138 · Longest Bitonic Subsequence
*Sheet: 02-08-2026 · Topic: DP · Pattern: LIS · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** LIS ending at i from the left and decreasing subsequence starting at i to the right; only count i when both are > 1 (strictly bitonic).
**Coach:** Good catch on the problem's specific rule.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 8 | 7 | 8 | 8 | **7.9** |

### #139 · Matrix Chain Multiplication
*Sheet: 02-08-2026 · Topic: DP · Pattern: MCM (interval DP/ range DP) · Difficulty H · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Interval DP: solve by length, try every split point k: cost = dp[i][k] + dp[k+1][j] + p[i−1]·p[k]·p[j]. Loops: length, start, split.
**Coach:** You explained that because only neighbours can be multiplied, the problem breaks into contiguous intervals. Well done.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 7 | 7 | 5 | 8 | **7.6** |

### #140 · 1547. Minimum Cost to Cut a Stick
*Sheet: 03-08-2026 · Topic: DP · Pattern: MCM (interval DP/ range DP) · Difficulty H · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Add 0 and n to the cuts and sort; dp over pairs of cut positions; the split is dp[i][k] + dp[k][j] (sharing k) because the pieces meet at a cut.
**Coach:** The k vs k+1 difference compared with matrix chain shows you understand what an interval means here.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 7 | 5 | 8 | **7.9** |

### #141 · 312. Burst Balloons
*Sheet: 06-08-2026 · Topic: DP · Pattern: MCM (interval DP/ range DP) · Difficulty H · Status S · 120 min · 4 revisions scheduled*
**Your thinking:** Choosing the *first* balloon to burst makes the two sides depend on each other. Choosing the *last* balloon in [i, j] separates them; its cost uses the boundaries nums[i−1]·nums[k]·nums[j+1]. Pad with 1s.
**Coach:** You explained *why* thinking about the last balloon works, the hardest insight in interval DP.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 8 | 9 | 8 | 7 | 3 | 8 | **7.8** |

### #143 · 132. Palindrome Partitioning II
*Sheet: 06-08-2026 · Topic: MCM + LIS · Pattern: min cuts to partition string into pallindromes · Difficulty H · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Precompute palindromes with interval DP, then a 1D minimum-cuts DP.
**Coach:** A good combination of two techniques; links back to #36.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 8 | 5 | 8 | **7.5** |

### #144 · 1277. Count Square Submatrices with All Ones
*Sheet: 06-08-2026 · Topic: DP on squares · Pattern: count all square submatrices of all 1s · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** dp[i][j] = 1 + min of the three neighbouring cells; it counts the squares with (i, j) as a corner. You note `if (matrix[m−1][n−1]) ans−−`.
**Coach:** That correction means your loop counts the corner cell twice. Fix the base case so no correction is needed.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 6 | 8 | 5 | 7 | 8 | 7 | **6.9** |

### #167 · AtCoder DP T - Permutation
*Sheet: 08-09-2026 · Topic: DP · Pattern: permutations using constraints · Difficulty H · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** dp[i][j] = arrangements of i items where the last has rank j; the actual values don't matter, only relative order, and inserting a new rank shifts the larger ones up. Prefix sums make each transition O(1); handle the modulo when subtracting.
**Coach:** A strong abstraction (only relative ranks matter) on a hard problem.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 8 | 8 | 5 | 8 | **7.9** |

### #176 · 1235. Maximum Profit in Job Scheduling
*Sheet: 13-09-2026 · Topic: DP + Binary Search · Pattern: find max profit by scheduling jobs · Difficulty H · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Sort by start; dp[i] = max(dp[i+1], profit[i] + dp[next]), with next found by binary search; set next = n if none, which removes the special case.
**Coach:** The "next = n" simplification is good engineering.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 8 | 5 | 8 | **7.9** |

### #196 · Count Palindromic Subsequences
*Sheet: 03-10-2026 · Topic: DP · Pattern: find number of pallindromic subsequences · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Interval DP with inclusion–exclusion: if s[i] != s[j], dp[i][j] = dp[i+1][j] + dp[i][j−1] − dp[i+1][j−1]; if equal, the subtraction cancels and you add 1 for the pair itself.
**Coach:** Deep inclusion–exclusion reasoning. Two fixes: your note has a typo (the second term should be dp[i][j−1]), and subtracting under a modulo needs `+ mod`.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 7 | 8 | 6 | 7 | 5 | 8 | **7.4** |

*#39 is under Recursion. #118 is under Trees.*

## Arrays & Hashing

### #145 · 189. Rotate Array
*Sheet: 08-08-2026 · Topic: Arrays · Pattern: rotate array by k places to the right · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Reverse the first n−k, reverse the last k, reverse the whole array.
**Coach:** Correct. Add `k %= n` first; it's the classic bug when k > n.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 6 | 7 | 5 | 7 | 8 | 7 | **6.6** |

### #146 · 283. Move Zeroes
*Sheet: 08-08-2026 · Topic: Arrays · Pattern: move all zeros to end · Difficulty E · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Each element moves left by the number of zeros before it, then fill the end with zeros.
**Coach:** A thoughtful counting view. The usual version swaps with a write pointer, which keeps order with fewer writes.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 6 | 7 | 6 | 5 | 7 | **6.6** |

### #147 · Longest Subarray with Sum K
*Sheet: 08-08-2026 · Topic: Arrays + Hashing · Pattern: find longest subarray with sum k · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Prefix sum plus hashmap: look up sum − k; store only the first index of each prefix sum (to maximise length). Strict order: add, look up, store.
**Coach:** Precise. Add when two pointers would also work (all positive numbers).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 7 | 5 | 8 | **7.6** |

### #148 · 560. Subarray Sum Equals K
*Sheet: 08-10-2026 · Topic: Arrays + Hashing · Pattern: number of subarrays with sum k · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Prefix-sum counts with mp[0] = 1; look up before inserting (otherwise k = 0 breaks). Key point: the sliding-window "at most K" trick doesn't work here because negative numbers break monotonicity.
**Coach:** The note on why sliding window fails is a top-tier transfer insight.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 10 | 8 | 7 | 5 | 9 | **8.1** |

### #149 · 53. Maximum Subarray
*Sheet: 09-08-2026 · Topic: Arrays + Hashing · Pattern: find max sum subarray · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Best sum ending here = current prefix minus the smallest earlier prefix; replace the map with one running minimum; Kadane as DP: dp[i] = max(dp[i−1] + a, a).
**Coach:** Three angles on one problem, ending with Kadane explained as DP, not memorised.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 8 | 5 | 9 | **8.1** |

### #150 · 75. Sort Colors
*Sheet: 09-08-2026 · Topic: Arrays · Pattern: Dutch National Flag Algorithm · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Dutch National Flag with four regions; at the start the 0, 1 and 2 regions are empty, so the rules hold trivially; when you swap a 0 in, mid moves too because what came from low is 1.
**Coach:** Explaining the algorithm through its loop invariant is the gold standard.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 9 | 8 | 9 | 8 | 4 | 9 | **8.2** |

### #151 · 169. Majority Element
*Sheet: 10-08-2026 · Topic: Arrays · Pattern: Boyer-Moore Voting Algorithm · Difficulty E · Status S · 20 min · 4 revisions scheduled*
**Your thinking:** Boyer-Moore: each majority element cancels one other element, and some majority elements must survive.
**Coach:** Good intuition. A small error: you wrote "count > n/2 + 1"; the definition is count > n/2.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 9 | 7 | 8 | 4 | 8 | **7.5** |

### #152 · 47. Permutations II
*Sheet: 10-08-2026 · Topic: Arrays · Pattern: Find all permutations when array contains duplicate elements · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Sort; skip nums[i] if it equals nums[i−1] and nums[i−1] isn't used yet. That forces equal values to be placed in a fixed order (2A before 2B before 2C), so duplicate permutations disappear.
**Coach:** The "fixed order for equal values" explanation is exactly why the condition works.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 9 | 8 | 7 | 5 | 9 | **8.0** |

### #153 · 31. Next Permutation
*Sheet: 10-08-2026 · Topic: Arrays · Pattern: Find next permutation · Difficulty M · Status S · 30 min · 4 revisions scheduled*
**Your thinking:** From the right, find the first i where nums[i] < nums[i+1]; swap it with the smallest larger value to its right; reverse everything after i. Your doc frames it as "the next larger number from the same digits".
**Coach:** Your sheet says "not intuitive, just learn it", but your doc does give the intuition (the suffix is already as large as possible). Trust the doc.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 8 | 8 | 8 | 7 | 7 | 4 | 8 | **7.2** |

### #154 · 128. Longest Consecutive Sequence
*Sheet: 11-08-2026 · Topic: Arrays + Hashing · Pattern: find the longest consecutive sequence · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Put everything in an unordered_set; only start counting from x when x−1 is missing; loop over the set, not the array, so duplicates don't repeat the work.
**Coach:** The set vs array iteration detail is a real performance insight.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 9 | 5 | 8 | **7.9** |

### #155 · 54. Spiral Matrix
*Sheet: 01-09-2026 · Topic: Arrays · Pattern: find spiral order of array · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Four boundaries; after each side, shrink one boundary and check the bounds again.
**Coach:** Good: the repeated boundary check is the whole trick.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 6 | 7 | 7 | 8 | 6 | 5 | 7 | **6.8** |

### #156 · 48. Rotate Image
*Sheet: 01-09-2026 · Topic: Arrays · Pattern: rotate image by 90degrees · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Clockwise: (i, j) goes to (j, n−1−i), which is transpose then reverse each row. Anticlockwise: transpose then reverse the order of rows. Derived on paper.
**Coach:** You derived the mapping, so you can work out any rotation.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 7 | 5 | 9 | **7.8** |

### #157 · 73. Set Matrix Zeroes
*Sheet: 01-09-2026 · Topic: Arrays · Pattern: set matrix zeroes · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Use the first row and column as markers; record first whether they originally had zeros; fill the inner cells; handle the first row and column last.
**Coach:** You explained the marker clash clearly.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 8 | 8 | 8 | 5 | 8 | **7.6** |

### #158 · 15. 3Sum
*Sheet: 02-09-2026 · Topic: Arrays · Pattern: 3 sum problem with duplicate handling · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Sort, fix i, two pointers on the rest. Rule: use the first occurrence of a value, then skip its duplicates, for i and for left/right after a match.
**Coach:** "Use first, then skip" is a rule you've applied in #34, #152 and #159.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 10 | 8 | 8 | 4 | 9 | **8.0** |

### #159 · 18. 4Sum
*Sheet: 02-09-2026 · Topic: Arrays · Pattern: 4 sum problem · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** One more loop; the inner duplicate check is `j > i+1`, not `j > 0`.
**Coach:** Good catch on `j > i+1`. Missing: on LeetCode the sum of four values near 1e9 overflows int, so use long long. Overflow has come up for you before (#44, #165).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 6 | 7 | 5 | 8 | **7.2** |

### #160 · 229. Majority Element II
*Sheet: 03-09-2026 · Topic: Arrays · Pattern: Boyer-Moore Voting Algorithm Extended · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** The "two podiums" analogy: matching values join, empty podiums are claimed, a third value removes one from each podium. Proof: at most n/3 such three-way removals, so a value with more than n/3 copies survives. Verify at the end. You extended it to n/4 with three podiums in code.
**Coach:** An original analogy plus a counting proof, then generalised. Excellent.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 9 | 10 | 8 | 8 | 4 | 9 | **8.4** |

### #161 · Count Subarrays with given XOR
*Sheet: 03-09-2026 · Topic: Arrays · Pattern: subarrays with given XOR · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Prefix XOR: look for the earlier prefix equal to current ^ k.
**Coach:** Direct transfer from #148.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 7 | 8 | 8 | **7.8** |

### #162 · 2588. Count the Number of Beautiful Subarrays
*Sheet: 03-09-2026 · Topic: Arrays · Pattern: count subarrays with XOR 0 · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** "Every bit appears an even number of times" means "XOR is 0", so it reduces to #161 with k = 0.
**Coach:** Spotting that reduction is the whole problem. Great.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 10 | 8 | 8 | 10 | 7 | 7 | 5 | 9 | **8.0** |

### #163 · Missing And Repeating
*Sheet: 04-09-2026 · Topic: Arrays · Pattern: find missing and repeating number in an array · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Use the difference of sums and the difference of sums of squares to solve two equations; be careful with long long.
**Coach:** Good. XOR partitioning is the other standard method.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 7 | 7 | 7 | 7 | 7 | 5 | 7 | **6.9** |

### #164 · 56. Merge Intervals
*Sheet: 04-09-2026 · Topic: Arrays · Pattern: sorting · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Sort by start; extend the last interval with max(end).
**Coach:** You noted why max matters (a nested interval).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 8 | 7 | 5 | 8 | **7.5** |

### #165 · 493. Reverse Pairs
*Sheet: 04-09-2026 · Topic: Arrays · Pattern: Divide and Conquer · Difficulty H · Status S · 50 min · 4 revisions scheduled*
**Your thinking:** Merge sort counting: count pairs between the two sorted halves *before* merging with a pointer that never resets (keeping it O(n)), then merge. You compared it with #47, where counting happens during the merge.
**Coach:** The comparison with #47 is excellent. Missing: `2 * nums[j]` overflows int, so cast to long long.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 10 | 7 | 9 | 4 | 8 | **8.0** |

### #166 · 152. Maximum Product Subarray
*Sheet: 04-09-2026 · Topic: Arrays · Pattern: max product subarray · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Take the best of the prefix product and suffix product, resetting to 1 at zeros; this automatically drops the leftmost or rightmost negative.
**Coach:** You explained *why* the prefix/suffix trick works by cases. Strong.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 8 | 8 | 5 | 8 | **7.9** |

## Two Pointers / Sliding Window

### #57 · The Celebrity Problem
*Sheet: 18-06-2026 · Topic: Two Pointers · Pattern: two pointers problem · Difficulty M · Status S · 30 min · 4 revisions scheduled*
**Your thinking:** There's at most one celebrity. Two pointers: if A knows B, A isn't the celebrity; otherwise B isn't. Then verify the survivor.
**Coach:** You proved "at most one" before writing the algorithm. Good.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 8 | 4 | 8 | **7.6** |

### #177 · 3. Longest Substring Without Repeating Characters
*Sheet: 19-09-2026 · Topic: Two Pointers · Pattern: find distinct character substring · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** A cryptic note about moving i and j when s[i] == s[j].
**Coach:** Too short to rebuild from. The standard version: store the last index of each character; left = max(left, last[c] + 1). Rewrite the note.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 4 | 3 | 7 | 6 | 6 | 8 | 5 | **5.9** |

### #178 · 1004. Max Consecutive Ones III
*Sheet: 19-09-2026 · Topic: Two Pointers · Pattern: find max consecutive ones · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Longest window with at most k zeros; a for loop plus an inner while loop; plan before coding.
**Coach:** Good.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 8 | 7 | 5 | 8 | **7.4** |

### #179 · 904. Fruit Into Baskets
*Sheet: 19-09-2026 · Topic: Two Pointers · Pattern: find largest subarray of 2 distinct elements only · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** You reused the Boyer-Moore "podium" idea: two fruit types with counts, and when a third appears, move the left pointer until one count reaches 0.
**Coach:** Creative transfer across topics. A frequency map that shrinks when its size goes above 2 is the standard, more general version.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 7 | 5 | 8 | **7.4** |

### #180 · 1248. Count Number of Nice Subarrays
*Sheet: 21-09-2026 · Topic: Two Pointers · Pattern: count the number of subarray that contain k odd elements · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Treat odd numbers as 1 and even as 0, then reuse binary subarrays with sum: atMost(k) − atMost(k−1).
**Coach:** Good reduction.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 9 | 7 | 7 | 5 | 8 | **7.4** |

### #181 · 930. Binary Subarrays With Sum
*Sheet: 21-09-2026 · Topic: Two Pointers · Pattern: count number of subarrays with given sum · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Prefix sums use O(n) space; with only 0s and 1s the prefix sums only go up, so a window works: atMost(goal) − atMost(goal−1); return 0 if goal < 0.
**Coach:** You named the reason (monotonicity) explicitly, which links it to #148.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 10 | 8 | 8 | 4 | 9 | **8.1** |

### #182 · Longest Substring with K Uniques
*Sheet: 25-09-2026 · Topic: Two Pointers · Pattern: find longest substring with K unique characters · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** A window with a frequency array and a count of distinct letters; shrink while above k; only record when exactly k.
**Coach:** Good; the "exactly k" check is the trap.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 8 | 7 | 5 | 8 | **7.4** |

### #183 · 1423. Maximum Points You Can Obtain from Cards
*Sheet: 25-09-2026 · Topic: Two Pointers · Pattern: find max by k cards from ends · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** Not DP: try taking i cards from the left and k−i from the right, updating the sum by sliding.
**Coach:** Good: you resisted overcomplicating it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 7 | 8 | 8 | 8 | **7.8** |

### #184 · 992. Subarrays with K Different Integers
*Sheet: 25-09-2026 · Topic: Two Pointers · Pattern: find count of subarrays with K different integers · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** atMost(K) − atMost(K−1); at most K distinct values is monotonic as the window grows or shrinks.
**Coach:** Good transfer, with monotonicity named again.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 10 | 7 | 8 | 5 | 9 | **8.0** |

### #185 · 1358. Number of Substrings Containing All Three Characters
*Sheet: 26-09-2026 · Topic: Two Pointers · Pattern: count number of substrings that contain all 3 characters · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Don't use the K-distinct machinery: track the last index of a, b and c; substrings ending at i = min(last) + 1.
**Coach:** Spotting that a more general tool is overkill is a mature skill. This one is due for revision today.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 8 | 8 | 5 | 8 | **7.9** |

### #186 · 424. Longest Repeating Character Replacement
*Sheet: 26-09-2026 · Topic: Two Pointers · Pattern: find longest substring you can form of same character by doing atmost K replacements · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** The window is valid if length − maxCount ≤ k. You never decrease maxCount, because the answer only grows when maxCount grows; a stale value only shifts the window along without making the answer wrong.
**Coach:** This stale-maxCount argument is among the hardest sliding-window ideas, and you explained it twice. Note: that explanation ended up in #187's revision column by mistake.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 10 | 8 | 9 | 8 | 9 | 4 | 9 | **8.2** |

### #187 · 76. Minimum Window Substring
*Sheet: 27-09-2026 · Topic: Two Pointers · Pattern: minimum window that contains all the characters of another string · Difficulty H · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Required counts vs window counts; shrink from the left while the leftmost character is surplus; replace the 128-character check with a `need` counter, giving O(m + n).
**Coach:** A good optimisation ladder. The revision note in this row is about #186, so move it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 9 | 4 | 8 | **7.8** |

### #188 · Minimum Window Subsequence
*Sheet: 27-09-2026 · Topic: Two Pointers · Pattern: minimum window subsequence · Difficulty M · Status S · 40 min · 4 revisions scheduled*
**Your thinking:** Go forward until the whole of s2 is matched as a subsequence, then go backward to find the latest start, record the window, and restart from start + 1.
**Coach:** A clear explanation of the forward/backward method. Worst case O(n·m); a DP version also exists.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 7 | 8 | 7 | 4 | 8 | **7.4** |

### #199 · 1297. Maximum Number of Occurrences of a Substring
*Sheet: 09-10-2026 · Topic: Two Pointers · Pattern: find max occurances of a substring · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** At most 26 distinct characters; only minSize matters (any longer valid substring contains a minSize one that occurs at least as often); then a sliding window of fixed size with distinct-character counts.
**Coach:** The "only minSize matters" reduction plus a step-by-step optimisation. Excellent.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 8 | 9 | 5 | 8 | **8.0** |

## Strings

### #189 · 205. Isomorphic Strings
*Sheet: 30-09-2026 · Topic: Strings · Pattern: check the conditions · Difficulty E · Status E · 10 min · 1 revisions scheduled*
**Your thinking:** Two maps (s→t and t→s) to enforce one-to-one.
**Coach:** Fine.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 6 | 7 | 8 | 6 | 8 | 8 | **7.2** |

### #190 · 796. Rotate String
*Sheet: 30-09-2026 · Topic: Strings · Pattern: check the conditions · Difficulty E · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** "Just brute force."
**Coach:** Learn the one-liner: `s.size() == goal.size() && (s + s).find(goal) != npos`. The sheet link goes to Valid Anagram; fix it.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 6 | 3 | 3 | 5 | 6 | 4 | 8 | 5 | **5.0** |

### #191 · 451. Sort Characters By Frequency
*Sheet: 30-09-2026 · Topic: Strings · Pattern: check the conditions · Difficulty E · Status E · 10 min · 1 revisions scheduled*
**Your thinking:** A note about ASCII values ('0' is 48, 0 is NULL).
**Coach:** Implementation trivia only. The method (count, then sort or bucket by frequency) isn't written down.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 7 | 3 | 3 | 5 | 6 | 4 | 8 | 5 | **5.1** |

### #192 · 5. Longest Palindromic Substring
*Sheet: 30-09-2026 · Topic: Strings · Pattern: find longest pallindromic substring · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** Interval DP O(n²) space, or expand around each centre (odd and even lengths) in O(1) space.
**Coach:** Good. Manacher's algorithm (O(n)) is optional, but worth knowing exists.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 8 | 8 | 5 | 8 | **7.5** |

### #193 · 1781. Sum of Beauty of All Substrings
*Sheet: 01-10-2026 · Topic: Strings · Pattern: find sum of beauty of all substrings · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** O(n³) to O(26·n²) by updating counts as the substring grows.
**Coach:** Good optimisation awareness; the note doesn't say how it's done.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 5 | 7 | 7 | 7 | 8 | 6 | **6.6** |

### #194 · 921. Minimum Add to Make Parentheses Valid
*Sheet: 02-10-2026 · Topic: Strings · Pattern: minimum parenthesis you need to add to make string valid · Difficulty M · Status H · 20 min · 3 revisions scheduled*
**Your thinking:** Inspired by #170: count an extra ')' immediately (it can never be matched) and add the leftover '(' at the end.
**Coach:** A direct transfer, and you said where the idea came from.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 10 | 8 | 7 | 5 | 8 | **7.9** |

### #195 · 38. Count and Say
*Sheet: 02-10-2026 · Topic: Strings · Pattern: follow the pattern · Difficulty M · Status E · 10 min · 1 revisions scheduled*
**Your thinking:** Recursion plus run-length encoding with two pointers.
**Coach:** Fine.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 5 | 6 | 7 | 5 | 8 | 6 | **6.2** |

### #202 · Minimum Deletion Span to Make a Subsequence (custom)
*Sheet: 11-10-2026 · Topic: Strings · Pattern: simple prefix suffix logic · Difficulty E · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** For each prefix, how much is matched as a subsequence; same for suffixes; delete one contiguous block. Heavy implementation.
**Coach:** The note has the problem statement but not your actual two-pointer method. Write it down: for each left, binary search or two-pointer to the best right.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 4 | 7 | 6 | 6 | 8 | 5 | **6.1** |

## Heaps

### #197 · Minimum Cost to Make Pods Distinct (custom)
*Sheet: 05-10-2026 · Topic: Heaps · Pattern: find minimum cost to make array unique · Difficulty M · Status H · 60 min · 3 revisions scheduled*
**Your thinking:** Go through IDs in increasing order; a max-heap by cost holds the pods currently at currId; the most expensive one keeps the ID and the rest move up by one; push new pods when currId reaches their ID.
**Coach:** A strong greedy with clear reasoning (IDs only go up, so go low to high). Add a short exchange argument for why the most expensive pod should stay.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 8 | 8 | 8 | 5 | 8 | **7.6** |

### #198 · 215. Kth Largest Element in an Array
*Sheet: 05-10-2026 · Topic: Heaps · Pattern: find K-th largest element · Difficulty M · Status E · 20 min · 1 revisions scheduled*
**Your thinking:** A size-k min-heap; its top is the k-th largest; O(n log k).
**Coach:** Good. Know quickselect (average O(n)) as the follow-up.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 7 | 8 | 8 | **8.0** |

### #203 · 621. Task Scheduler
*Sheet: 18-10-2026 · Topic: Heaps · Pattern: schedule tasks · Difficulty M · Status H · 60 min · 3 revisions scheduled*
**Your thinking:** Simulate in blocks of n+1 slots, taking the most frequent tasks first from a max-heap, holding used tasks out of the heap until the block ends; the last block counts only its actual length.
**Coach:** The simulation is right. Also learn the O(1) formula: max(len, (maxFreq − 1)·(n + 1) + number of tasks with maxFreq).
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 8 | 8 | 6 | 5 | 8 | **7.4** |

### #212 · Room Allocation (CSES)
*Sheet: 27-10-2026 · Topic: Heaps · Pattern: allocate minimum possible rooms to people · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Sort by arrival; a min-heap of (end time, room); reuse the earliest free room if it's free before the arrival, otherwise open a new one.
**Coach:** Good.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 7 | 7 | 8 | 8 | **7.6** |

## Sorting, Counting & CSES

### #205 · Concert Tickets (CSES)
*Sheet: 24-10-2026 · Topic: Sorting · Pattern: use multiset · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** A multiset; the largest price ≤ offer is `prev(upper_bound)`; if upper_bound is begin, print −1; erase the ticket.
**Coach:** A precise STL idiom. Due for revision today.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 8 | 8 | 5 | 8 | **7.8** |

### #206 · Missing Coin Sum (CSES)
*Sheet: 24-10-2026 · Topic: Sorting · Pattern: solve without dp · Difficulty M · Status H · 40 min · 3 revisions scheduled*
**Your thinking:** Sort; if every sum up to S is reachable and the next coin a ≤ S + 1, then everything up to S + a is reachable; otherwise S + 1 is the answer.
**Coach:** An induction argument. Your note splits a < S and a == S or S+1; just write a ≤ S + 1. Due for revision today.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 8 | 8 | 8 | 8 | 5 | 8 | **7.9** |

### #207 · Traffic Lights (CSES)
*Sheet: 25-10-2026 · Topic: Sorting · Pattern: find max gap between array elements after adding new element at each step · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Online: a set of positions plus a multiset of gap lengths. Better: process in reverse, removing lights so gaps only grow.
**Coach:** Thinking in reverse is a powerful general technique.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 9 | 7 | 8 | 8 | 8 | **8.1** |

### #209 · Distinct Values Subsequences (CSES)
*Sheet: 26-10-2026 · Topic: Counting · Pattern: think beyond just building subsequence and towards counting · Difficulty M · Status H · 30 min · 3 revisions scheduled*
**Your thinking:** For each distinct value with m copies there are m + 1 choices (pick one copy or none); multiply and subtract 1 for the empty subsequence.
**Coach:** Clear counting. Watch the modulo.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 7 | 7 | 5 | 8 | **7.5** |

### #210 · Collecting Numbers II (CSES)
*Sheet: 26-10-2026 · Topic: Queries · Pattern: solve queries directly · Difficulty M · Status E · 40 min · 1 revisions scheduled*
**Your thinking:** A swap only affects the neighbours of the two values (four pairs, stored in a set); answer += new contribution − old.
**Coach:** A local-update approach to queries.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 7 | 7 | 8 | 8 | 7 | 8 | 7 | **7.6** |

### #211 · Nested Ranges Check (CSES)
*Sheet: 27-10-2026 · Topic: Sorting · Pattern: sort and solve range queries in single pass · Difficulty M · Status H · 60 min · 3 revisions scheduled*
**Your thinking:** Sort by left end ascending, and by right end descending on ties. Left to right with the largest right end seen so far: a range is contained in another if its right end is ≤ that maximum. Right to left with the smallest right end seen: a range contains another if its right end is ≥ that minimum. Print in the original order.
**Coach:** You explained why the tie-break on the right end matters. A two-pass sweep.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 8 | 8 | 8 | 5 | 8 | **7.6** |

### #213 · Tasks and Deadlines (CSES)
*Sheet: 27-10-2026 · Topic: Sorting · Pattern: write out things on paper first · Difficulty M · Status E · 40 min · 1 revisions scheduled*
**Your thinking:** Write the objective down: the sum of deadlines is fixed, so you minimise the sum of finish times, which means doing shortest tasks first.
**Coach:** Writing the formula down was what cracked it. Remember the result needs long long.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 8 | 8 | 7 | 7 | 8 | 8 | **7.9** |

### #214 · Reading Books (CSES)
*Sheet: 28-10-2026 · Topic: Lower bound & scheduling problem · Pattern: schedule tasks · Difficulty M · Status E · 30 min · 1 revisions scheduled*
**Your thinking:** Your handwritten cases: if the longest book is at least the total of the others, the answer is 2·max; otherwise it's the total. Both readers can always stay busy.
**Coach:** A case split with a timeline drawing.
| Pattern | Why | Clarity | Transfer | Edge | Complexity | Independence | Retention | **Overall** |
|---|---|---|---|---|---|---|---|---|
| 9 | 8 | 7 | 7 | 7 | 8 | 8 | 8 | **7.8** |
