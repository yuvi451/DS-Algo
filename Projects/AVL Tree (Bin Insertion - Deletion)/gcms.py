from bin import Bin
from avl import AVLTree
from object import Object, Color
from exceptions import NoBinFoundException


def comp1(root, key):
    if root.key.bin_capacity > key.bin_capacity or (root.key.bin_capacity == key.bin_capacity and root.key.id > key.id):
        return 0
    return 1
def comp2(root, key):
    if root.key.id > key.id:
        return 0
    return 1

def comp3(root, key):
    if root.key.bin_capacity > key.bin_capacity or (root.key.bin_capacity == key.bin_capacity and root.key.id < key.id):
        return 0
    return 1


class GCMS:
    def __init__(self):
        self.Tree = AVLTree(comp1)
        self.Tree1 = AVLTree(comp3)
        self.Object_ID = AVLTree(comp2)
        self.Bin_ID = AVLTree(comp2)

    def add_bin(self, bin_id, capacity):
        bin = Bin(bin_id, capacity)
        self.Tree.root = self.Tree.insert(self.Tree.root, bin)
        self.Tree1.root = self.Tree1.insert(self.Tree1.root, bin)
        self.Bin_ID.root = self.Bin_ID.insert(self.Bin_ID.root, bin)

    def add_object(self, object_id, size, color):
        cargo = Object(object_id, size, color)
        node = None
        if color == Color.BLUE or color == Color.GREEN:
            node = self.Tree.Cargo(self.Tree.root, cargo, color, node)
        else:
            node = self.Tree1.Cargo(self.Tree1.root, cargo, color, node)
        if node is None:
            raise NoBinFoundException()

        bin = node.key

        self.Tree.root = self.Tree.delete(self.Tree.root, bin)
        self.Tree1.root = self.Tree1.delete(self.Tree1.root, bin)

        bin.add_object(cargo)

        self.Tree.root = self.Tree.insert(self.Tree.root, bin)
        self.Tree1.root = self.Tree1.insert(self.Tree1.root, bin)
        self.Object_ID.root = self.Object_ID.insert(self.Object_ID.root, cargo)

    def delete_object(self, object_id):
        obj_node = self.Object_ID.search_1(self.Object_ID.root, object_id)
        if obj_node is not None:
            bin_id = obj_node.key.bin_id
            bin_node = self.Bin_ID.search_1(self.Bin_ID.root, bin_id)

            bin = bin_node.key

            bin_node_1 = self.Tree.search(self.Tree.root, bin)

            bin_1 = bin_node_1.key

            self.Tree.root = self.Tree.delete(self.Tree.root, bin_1)
            self.Tree1.root = self.Tree1.delete(self.Tree1.root, bin_1)

            bin_1.remove_object(object_id)

            self.Tree.root = self.Tree.insert(self.Tree.root, bin_1)
            self.Tree1.root = self.Tree1.insert(self.Tree1.root, bin_1)

            self.Object_ID.root = self.Object_ID.delete_1(self.Object_ID.root, obj_node.key)

    def bin_info(self, bin_id):
        a = self.Bin_ID.search_1(self.Bin_ID.root, bin_id)
        b = a.key.inorder_traversal(a.key.BinTree.root)
        return (a.key.bin_capacity, b)

    def object_info(self, object_id):
        a = self.Object_ID.search_1(self.Object_ID.root, object_id)
        if a is not None:
            return a.key.bin_id
