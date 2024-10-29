class HashTable:
    def __init__(self, collision_type, params):
        self.collision_type = collision_type
        self.params = params
        self.table_size = self.params[-1]
        self.table = [None] * self.table_size
        self.count = 0

    def str_to_int(self, x):
        if ord(x) >= ord('a'):
            return ord(x) - ord('a')
        else:
            return ord(x) - ord('A') + 26

    def _hash(self, x, z):
        h = 0
        for i in range(len(x)):
            h += (z ** i) * (self.str_to_int(x[i]))
        return h

    def get_load(self):
        return (self.count / self.table_size)

    def get_slot(self, key):
        z1 = self.params[0]
        index = self._hash(key, z1) % self.table_size

        if self.collision_type == "Chain":
            return index

        elif self.collision_type == "Linear":
            while self.table[index] != key:
                index = (index + 1) % self.table_size
            return index

        else:
            z2 = self.params[1]
            c2 = self.params[2]
            step = c2 - (self._hash(key, z2) % c2)
            original_index = index
            j = 1
            while self.table[index] != key:
                index = (original_index + j * step) % self.table_size
                j += 1
            return index

class HashSet(HashTable):
    def __init__(self, collision_type, params):
        self.collision_type = collision_type
        self.params = params
        self.table_size = self.params[-1]
        self.table = [None] * self.table_size
        self.count = 0

    def insert(self, x):
        z = self.params[0]
        index = self._hash(x, z) % self.table_size
        original_index = index

        if self.collision_type == "Chain":
            if self.table[index] is None:
                self.table[index] = []
            for i in self.table[index]:
                if i == x: return
            self.table[index].append(x)
            self.count += 1

        elif self.collision_type == "Linear":
            while self.table[index] is not None:
                if self.table[index] == x:
                    return
                index = (index + 1) % self.table_size
                if index == original_index: return
            self.count += 1
            self.table[index] = x

        else:
            z2 = self.params[1]
            c2 = self.params[2]
            step = c2 - (self._hash(x, z2) % c2)
            j = 1
            while self.table[index] is not None:
                if self.table[index] == x:
                    return
                index = (original_index + j * step) % self.table_size
                j += 1
                if index == original_index: return
            self.count += 1
            self.table[index] = x


    def find(self, key):
        z1 = self.params[0]
        index = self._hash(key, z1) % self.table_size
        original_index = index

        if self.collision_type == "Chain":
            if self.table[index]:
                for i in self.table[index]:
                    if i == key: return True
            return False

        elif self.collision_type == "Linear":
            while self.table[index] is not None and self.table[index] != key:
                index = (index + 1) % self.table_size
                if original_index == index: break
            if self.table[index] is None or self.table[index] != key:
                return False
            return True

        else:
            if self.table[index] is not None:
                z2 = self.params[1]
                c2 = self.params[2]
                step = c2 - (self._hash(key, z2) % c2)
                j = 1
                while self.table[index] is not None and self.table[index] != key:
                    index = (original_index + j * step) % self.table_size
                    j += 1
                    if index == original_index: break
            if self.table[index] is None or self.table[index] != key:
                return False
            return True

    def __str__(self):
        s = ''
        if self.collision_type == "Chain":
            c = 0
            for i in self.table:
                c += 1
                if i is None:
                    s += '<EMPTY>'
                else:
                    d = 0
                    for j in i:
                        d += 1
                        s += str(j)
                        if d < len(i):
                            s += ' ; '

                if c < self.table_size:
                    s += ' | '
        else:
            c = 0
            for i in self.table:
                c += 1
                if i is None:
                    s += '<EMPTY>'
                else:
                    s += str(i)

                if c < self.table_size:
                    s += ' | '
        return s


class HashMap(HashTable):
    def __init__(self, collision_type, params):
        self.collision_type = collision_type
        self.params = params
        self.table_size = self.params[-1]
        self.table = [None] * self.table_size
        self.count = 0

    def insert(self, x):
        z = self.params[0]
        index = self._hash(x[0], z) % self.table_size
        original_index = index

        if self.collision_type == "Chain":
            if self.table[index] is None:
                self.table[index] = []
            self.table[index].append(x)
            self.count += 1

        elif self.collision_type == "Linear":
            while self.table[index] is not None:
                index = (index + 1) % self.table_size
                if index == original_index: return
            self.count += 1
            self.table[index] = x

        else:
            z2 = self.params[1]
            c2 = self.params[2]
            step = c2 - (self._hash(x[0], z2) % c2)
            j = 1
            while self.table[index] is not None:
                index = (original_index + j * step) % self.table_size
                j += 1
                if index == original_index: return
            self.count += 1
            self.table[index] = x

    def find(self, key):
        z1 = self.params[0]
        index = self._hash(key, z1) % self.table_size
        original_index = index

        if self.collision_type == "Chain":
            if self.table[index]:
                for i in self.table[index]:
                     if i[0] == key: return i[1]
            return None

        elif self.collision_type == "Linear":
            while self.table[index] is not None and self.table[index][0] != key:
                index = (index + 1) % self.table_size
                if original_index == index: break
            if self.table[index] is None or self.table[index][0] != key:
                return None
            return self.table[index][1]

        else:
            if self.table[index] is not None:
                z2 = self.params[1]
                c2 = self.params[2]
                step = c2 - (self._hash(key, z2) % c2)
                j = 1
                while self.table[index] is not None and self.table[index][0] != key:
                    index = (original_index + j * step) % self.table_size
                    j += 1
                    if index == original_index: break
            if self.table[index] is None or self.table[index][0] != key:
                return None
            return self.table[index][1]

    def __str__(self):
        s = ''
        if self.collision_type == "Chain":
            c = 0
            for i in self.table:
                c += 1
                if i is None:
                    s += '<EMPTY>'
                else:
                    d = 0
                    for j in i:
                        d += 1
                        s += f'({j[0]}, {j[1]})'
                        if d < len(i):
                            s += ' ; '

                if c < self.table_size:
                    s += ' | '
        else:
            c = 0
            for i in self.table:
                c += 1
                if i is None:
                    s += '<EMPTY>'
                else:
                    s += f'({i[0]}, {i[1]})'

                if c < self.table_size:
                    s += ' | '
        return s



