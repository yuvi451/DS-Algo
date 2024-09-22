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
