class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

    def insert(self, value):
        if value < self.value:
            if self.left:
                self.left.insert(value)
            else:
                self.left = Node(value)
        else:
            if self.right:
                self.right.insert(value)
            else:
                self.right = Node(value)

    def inorder_traversal(self):
        if self.left:
            self.left.inorder_traversal()
        print(self.value)
        if self.right:
            self.right.inorder_traversal()

    def find(self, value):
        if value == self.value: return True
        elif value < self.value:
            if self.left:
                return self.left.find(value)
            else:
                return False
        else:
            if self.right:
                return self.right.find(value)
            else:
                return False

    def delete(self, value):
        if value < self.value:
            if self.left:
                self.left = self.left.delete(value)  # Recurse into left subtree : left node = .... recurive_fn()
        elif value > self.value:
            if self.right:
                self.right = self.right.delete(value)  # Recurse into right subtree : right node = .... recursive_fn()
        else:
            # Node to be deleted is found
            if self.left is None:  # Case 1: No left child, or Case 2: Only right child
                return self.right   # if No right node : returns None otherwise right node
            elif self.right is None:  # Case 2: Only left child
                return self.left     # if No left node : returns None otherwise left node
            # Case 3: Node has two children
            min_larger_node = self._min_value_node(self.right)  # In-order successor
            self.value = min_larger_node.value  # Replace node's value with successor's value
            self.right = self.right.delete(min_larger_node.value)  # Delete the in-order successor

        return self

    def _min_value_node(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current


class BST(Node):
    def __init__(self):
        self.root = None

    def insert(self, value):
        if self.root is None:
            self.root = Node(value)
        else:
            self.root.insert(value)

    def inorder_traversal(self):
        self.root.inorder_traversal()

    def find(self, value):
        return self.root.find(value)

    def delete(self, value):
        self.root.delete(value)





--------   OR   --------





class TreeNode:

    def __init__(self, value):
        self.left = None
        self.right = None
        self.value = value
        self.content = None

    def insert(self, value, content = None):
        if value < self.value:
            if self.left is None:
                self.left = TreeNode(value) # once it finds an appropriate empty spot it places it there as a node object
                self.left.content = content
            else:
                self.left.insert(value, content) # recursively call it for the root of the subtree on left
        else:
            if self.right is None:
                self.right = TreeNode(value) # once it finds an appropriate empty spot it places it there as a node object
                self.right.content = content
            else:
                self.right.insert(value, content) # recursively call it for the root of the subtree on right

    def inorder_traversal(self):
        if self.left:
            self.left.inorder_traversal()
        print(self.value)
        if self.right:
            self.right.inorder_traversal()

    def preorder_traversal(self):
        print(self.value)
        if self.left:
            self.left.preorder_traversal()
        if self.right:
            self.right.preorder_traversal()

    def postorder_traversal(self):
        if self.left:
            self.left.postorder_traversal()
        if self.right:
            self.right.postorder_traversal()
        print(self.value)

    def find(self, value):
        if value == self.value:
            return True
        elif value < self.value:
            if self.left:
                return self.left.find(value)
            else: return False
        else:
            if self.right:
                return self.right.find(value)
            else: return False


# every node can be visualised as a root of a subtree which is connected to other nodes
# TreeNode function initialises a node (object) i.e. root of a subtree
# the first object created once we initialise a tree is the root of the overall tree
# Whenver an element is to be inserted it first compares itself to the overall root and then traverses down recursively
# node is always inserted as a leaf. Whenever we call tree.insert() we are calling it for root node i.e. connect it to the root node. If not
# traverse down recursively
# tree.value is the value of overall root of the tree && tree is the overall root node object: tree.left, tree.right, tree.left.left.....
# are some of the other node objects (that are connected)
# This tree implementation is not a list but a collection of connected objects i.e. nodes (multidimensional linked list)


tree = TreeNode(30)
tree.insert(10)
tree.insert(20)
tree.insert(40)
tree.insert(50)
tree.insert(60)
tree.insert(70)

print(tree.find(45))
# we can also initialse in such a way that when it finds a node it returns the node object
# from this node object we can access the content
# AVL Tree is a balanced binary tree
