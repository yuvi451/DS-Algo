from hash_table import HashSet, HashMap
from prime_generator import get_next_size

class DynamicHashSet(HashSet):
    def __init__(self, collision_type, params):
        self.collision_type = collision_type
        self.params = params
        super().__init__(collision_type, params)

    def rehash(self):
        new_size = get_next_size()
        old_table = self.table[:]
        self.table_size = new_size
        self.table = [None] * self.table_size
        z = self.params[0]

        for i in old_table:
            if i is not None:
                if self.collision_type == "Chain":
                    for element in i:
                        index = self._hash(element, z) % self.table_size
                        if self.table[index] is None:
                            self.table[index] = []
                        self.table[index].append(element)

                elif self.collision_type == "Linear":
                    index = self._hash(i, z) % self.table_size
                    while self.table[index] is not None:
                        index = (index + 1) % self.table_size
                    self.table[index] = i

                else:
                    z2 = self.params[1]
                    c2 = self.params[2]
                    step = c2 - (self._hash(i, z2) % c2)
                    j = 1
                    index = self._hash(i, z) % self.table_size
                    original_index = index
                    while self.table[index] is not None:
                        index = (original_index + j * step) % self.table_size
                        j += 1
                    self.table[index] = i

    def insert(self, key):
        super().insert(key)
        
        if self.get_load() >= 0.5:
            self.rehash()
            
            
class DynamicHashMap(HashMap):
    def __init__(self, collision_type, params):
        self.collision_type = collision_type
        self.params = params
        super().__init__(collision_type, params)

    def rehash(self):
        new_size = get_next_size()
        old_table = self.table[:]
        self.table_size = new_size
        self.table = [None] * self.table_size
        z = self.params[0]

        for i in old_table:
            if i is not None:
                if self.collision_type == "Chain":
                    for key, value in i:
                        index = self._hash(key, z) % self.table_size
                        if self.table[index] is None:
                            self.table[index] = []
                        self.table[index].append((key, value))

                elif self.collision_type == "Linear":
                    key, value = i
                    index = self._hash(key, z) % self.table_size
                    while self.table[index] is not None:
                        index = (index + 1) % self.table_size
                    self.table[index] = (key, value)

                else:
                    key, value = i
                    z2 = self.params[1]
                    c2 = self.params[2]
                    step = c2 - (self._hash(key, z2) % c2)
                    j = 1
                    index = self._hash(key, z) % self.table_size
                    original_index = index
                    while self.table[index] is not None:
                        index = (original_index + j * step) % self.table_size
                        j += 1
                    self.table[index] = (key, value)


    def insert(self, key):
        super().insert(key)
        
        if self.get_load() >= 0.5:
            self.rehash()



