class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.height = 1

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

        # Update the height of the current node
        self.height = 1 + max(self._get_height(self.left), self._get_height(self.right))

        # Balance the node if it's unbalanced
        balance = self._get_balance()

        # Left Left Case
        if balance > 1 and value < self.left.value:
            return self.right_rotate()

        # Right Right Case
        if balance < -1 and value > self.right.value:
            return self.left_rotate()

        # Left Right Case
        if balance > 1 and value > self.left.value:
            self.left = self.left.left_rotate()
            return self.right_rotate()

        # Right Left Case
        if balance < -1 and value < self.right.value:
            self.right = self.right.right_rotate()
            return self.left_rotate()

        return self

    def inorder_traversal(self):
        if self.left:
            self.left.inorder_traversal()
        print(self.value)
        if self.right:
            self.right.inorder_traversal()

    def find(self, value):
        if value == self.value:
            return True
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
                self.left = self.left.delete(value)
        elif value > self.value:
            if self.right:
                self.right = self.right.delete(value)
        else:
            if self.left is None:
                return self.right
            elif self.right is None:
                return self.left
            min_larger_node = self._min_value_node(self.right)
            self.value = min_larger_node.value
            self.right = self.right.delete(min_larger_node.value)

        if not self:
            return None

        # Update the height
        self.height = 1 + max(self._get_height(self.left), self._get_height(self.right))

        # Balance the node
        balance = self._get_balance()

        # Left Left Case
        if balance > 1 and self._get_balance(self.left) >= 0:
            return self.right_rotate()

        # Left Right Case
        if balance > 1 and self._get_balance(self.left) < 0:
            self.left = self.left.left_rotate()
            return self.right_rotate()

        # Right Right Case
        if balance < -1 and self._get_balance(self.right) <= 0:
            return self.left_rotate()

        # Right Left Case
        if balance < -1 and self._get_balance(self.right) > 0:
            self.right = self.right.right_rotate()
            return self.left_rotate()

        return self

    def _min_value_node(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current

    def _get_height(self, node):
        if not node:
            return 0
        return node.height

    def _get_balance(self):
        return self._get_height(self.left) - self._get_height(self.right)

    def left_rotate(self):
        y = self.right
        T2 = y.left

        # Perform rotation
        y.left = self
        self.right = T2

        # Update heights
        self.height = 1 + max(self._get_height(self.left), self._get_height(self.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        return y

    def right_rotate(self):
        y = self.left
        T3 = y.right

        # Perform rotation
        y.right = self
        self.left = T3

        # Update heights
        self.height = 1 + max(self._get_height(self.left), self._get_height(self.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        return y


class AVLTree:
    def __init__(self):
        self.root = None

    def insert(self, value):
        if self.root is None:
            self.root = Node(value)
        else:
            self.root = self.root.insert(value)

    def inorder_traversal(self):
        if self.root:
            self.root.inorder_traversal()

    def find(self, value):
        return self.root.find(value) if self.root else False

    def delete(self, value):
        if self.root:
            self.root = self.root.delete(value)
