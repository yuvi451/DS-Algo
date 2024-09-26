from avl import AVLTree

def comp2(root, key):
    if root.key.id > key.id:
        return 0
    return 1


class Bin:
    def __init__(self, bin_id, capacity):
        self.id = bin_id
        self.bin_capacity = capacity
        self.BinTree = AVLTree(comp2)

    def add_object(self, object):
        self.bin_capacity -= object.size
        object.bin_id = self.id
        self.BinTree.root = self.BinTree.insert(self.BinTree.root, object)

    def remove_object(self, object_id):
        a = self.BinTree.search_1(self.BinTree.root, object_id)
        self.bin_capacity += a.key.size
        self.BinTree.root = self.BinTree.delete_1(self.BinTree.root, a.key)
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
