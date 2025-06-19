class Heap:

    def __init__(self, comparison_function, init_array):
        self.comparator = comparison_function
        self.heap = init_array[:]
        for i in range(len(self.heap) - 1, -1, -1):
            self._shift_down(i)

    def _shift_up(self, i):
        parent = (i - 1) // 2
        while i != 0 and self.comparator(self.heap[i], self.heap[parent]):
            self.heap[i], self.heap[parent] = self.heap[parent], self.heap[i]
            i = parent
            parent = (i - 1) // 2

    def _shift_down(self, i):
        left = 2*i + 1
        right = 2*i + 2
        while (left < len(self.heap) and self.comparator(self.heap[left], self.heap[i])) or (
                right < len(self.heap) and self.comparator(self.heap[right], self.heap[i])):
            t = left if (right >= len(self.heap) or self.comparator(self.heap[left], self.heap[right])) else right
            self.heap[i], self.heap[t] = self.heap[t], self.heap[i]
            i = t
            left = 2*i + 1
            right = 2*i + 2

    def insert(self, value):
        self.heap.append(value)
        self._shift_up(len(self.heap) - 1)

    def extract(self):
        if len(self.heap) == 0:
            return None
        val = self.heap[0]
        self.heap[0], self.heap[-1] = self.heap[-1], self.heap[0]
        self.heap.pop()
        self._shift_down(0)
        return val

    def top(self):
        return self.heap[0] if len(self.heap) > 0 else None
