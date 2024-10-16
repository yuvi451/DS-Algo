
from node import Node
from object import Color

class AVLTree:
    def __init__(self, compare_function):
        self.root = None
        self.comparator = compare_function

    def _height(self, node):
        if node is None:
            return 0
        return node.height

    def _update_height(self, node):
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance_factor(self, node):
        if node is None:
            return 0
        return self._height(node.left) - self._height(node.right)

    def _rotate_right(self, y):
        if y.left is None:
            return None

        x = y.left
        T2 = x.right

        x.right = y
        y.left = T2

        y.height = 1 + max(self._height(y.left), self._height(y.right))
        x.height = 1 + max(self._height(x.left), self._height(x.right))

        return x

    def _rotate_left(self, x):
        if x.right is None:
            return None

        y = x.right
        T2 = y.left

        y.left = x
        x.right = T2

        x.height = 1 + max(self._height(x.left), self._height(x.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))

        return y

    def insert(self, root, key):
        if root is None:
            return Node(key)

        comparison = self.comparator(root, key)

        if comparison == 0:
            root.left = self.insert(root.left, key)
        else:
            root.right = self.insert(root.right, key)

        self._update_height(root)

        balance = self._balance_factor(root)

        if balance > 1:
            if self.comparator(root.left, key) == 0:
                return self._rotate_right(root)
            else:
                root.left = self._rotate_left(root.left)
                return self._rotate_right(root)

        if balance < -1:
            if self.comparator(root.right, key) == 1:
                return self._rotate_left(root)
            else:
                root.right = self._rotate_right(root.right)
                return self._rotate_left(root)

        return root

    def _minimum_left_node_on_right_subtree(self, node):
        x = node.right
        while x.left is not None:
            x = x.left
        return x

    def Cargo(self, root, cargo, color, best_fit_node):
        if root is None:
            return best_fit_node

        bin_capacity = root.key.bin_capacity

        if bin_capacity >= cargo.size:

            if best_fit_node is None:
                best_fit_node = root

            if color == Color.BLUE or color == Color.YELLOW:
                best_fit_node = root
                return self.Cargo(root.left, cargo, color, best_fit_node)

            if color == Color.GREEN or color == color.RED:
                best_fit_node = root
                return self.Cargo(root.right, cargo, color, best_fit_node)

        else:
            return self.Cargo(root.right, cargo, color, best_fit_node)

    def delete(self, root, key):
        if root is None:
            return root

        comparison = self.comparator(root, key)

        if comparison == 0:
            root.left = self.delete(root.left, key)
        elif comparison == 1:
            root.right = self.delete(root.right, key)

        if root.key.bin_capacity == key.bin_capacity and root.key.id == key.id:
            if root.left is None:
                return root.right
            elif root.right is None:
                return root.left

            temp = self._minimum_left_node_on_right_subtree(root)
            root.key = temp.key
            root.right = self.delete(root.right, temp.key)

        if root is None:
            return root

        self._update_height(root)

        balance = self._balance_factor(root)

        if balance > 1:
            if self._balance_factor(root.left) >= 0:
                return self._rotate_right(root)
            else:
                root.left = self._rotate_left(root.left)
                return self._rotate_right(root)

        if balance < -1:
            if self._balance_factor(root.right) <= 0:
                return self._rotate_left(root)
            else:
                root.right = self._rotate_right(root.right)
                return self._rotate_left(root)

        return root

    def inorder_traversal(self, root, lis=None):
        if lis is None:
            lis = []

        if root is not None:
            if root.left:
                self.inorder_traversal(root.left, lis)
            lis.append(root.key.id)
            if root.right:
                self.inorder_traversal(root.right, lis)

        return lis

    def search(self, root, key):
        if root is None:
            return None

        if root.key.bin_capacity == key.bin_capacity and root.key.id == key.id:
            return root

        comparison = self.comparator(root, key)

        if comparison == 0:
            return self.search(root.left, key)
        return self.search(root.right, key)

    def search_1(self, root, key):
        if root is None or root.key.id == key: return root
        if root.key.id > key: return self.search_1(root.left, key)
        return self.search_1(root.right, key)

    def delete_1(self, root, key):
        if root is None:
            return root

        comparison = self.comparator(root, key)

        if comparison == 0:
            root.left = self.delete_1(root.left, key)
        elif comparison == 1:
            root.right = self.delete_1(root.right, key)

        if root.key.id == key.id:
            if root.left is None:
                return root.right
            elif root.right is None:
                return root.left

            temp = self._minimum_left_node_on_right_subtree(root)
            root.key = temp.key
            root.right = self.delete_1(root.right, temp.key)

        if root is None:
            return root

        self._update_height(root)

        balance = self._balance_factor(root)

        if balance > 1:
            if self._balance_factor(root.left) >= 0:
                return self._rotate_right(root)
            else:
                root.left = self._rotate_left(root.left)
                return self._rotate_right(root)

        if balance < -1:
            if self._balance_factor(root.right) <= 0:
                return self._rotate_left(root)
            else:
                root.right = self._rotate_right(root.right)
                return self._rotate_left(root)

        return root
