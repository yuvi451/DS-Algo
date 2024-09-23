class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 1

class AVLTree:
    def __init__(self):
        self.root = None

    def _height(self, node):
        if not node:
            return 0
        return node.height

    def _right_rotate(self, y):
        x = y.left
        T2 = x.right

        x.right = y
        y.left = T2

        y.height = 1 + max(self._height(y.left), self._height(y.right))
        x.height = 1 + max(self._height(x.left), self._height(x.right))

        return x

    def _left_rotate(self, x):
        y = x.right
        T2 = y.left

        y.left = x
        x.right = T2

        x.height = 1 + max(self._height(x.left), self._height(x.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))

        return y

    def insert(self, root, key):
        if not root:
            return Node(key)
        elif key < root.key:
            root.left = self.insert(root.left, key)
        else:
            root.right = self.insert(root.right, key)

        root.height = 1 + max(self._height(root.left), self._height(root.right))

        balance = self._height(root.left) - self._height(root.right)

        if balance > 1 and key < root.left.key:
            return self._right_rotate(root)

        if balance < -1 and key > root.right.key:
            return self._left_rotate(root)

        if balance > 1 and key > root.left.key:
            root.left = self._left_rotate(root.left)
            return self._right_rotate(root)

        if balance < -1 and key < root.right.key:
            root.right = self._right_rotate(root.right)
            return self._left_rotate(root)

        return root

    def _minimum_left_node_on_right_subtree(self, node):
        x = node.right
        while x.left is not None:
            x = x.left
        return x

    def delete(self, root, key):
        if not root:
            return root
        elif key < root.key:
            root.left = self.delete(root.left, key)
        elif key > root.key:
            root.right = self.delete(root.right, key)
        else:
            if root.left is None:
                return root.right
            elif root.right is None:
                return root.left

            temp = self._minimum_left_node_on_right_subtree(root)
            root.key = temp.key
            root.right = self.delete(root.right, temp.key)

        if root is None:
            return root

        root.height = 1 + max(self._height(root.left), self._height(root.right))

        balance = self._height(root.left) - self._height(root.right)

        if balance > 1 and self._height(root.left.left) >= self._height(root.left.right):
            return self._right_rotate(root)

        if balance > 1 and self._height(root.left.left) < self._height(root.left.right):
            root.left = self._left_rotate(root.left)
            return self._right_rotate(root)

        if balance < -1 and self._height(root.right.right) >= self._height(root.right.left):
            return self._left_rotate(root)

        if balance < -1 and self._height(root.right.right) < self._height(root.right.left):
            root.right = self._right_rotate(root.right)
            return self._left_rotate(root)

        return root



tree = AVLTree()
for i in range(2, 17):
    tree.root = tree.insert(tree.root, i)
tree.delete(tree.root, 5)
print(tree.root.left.key)
