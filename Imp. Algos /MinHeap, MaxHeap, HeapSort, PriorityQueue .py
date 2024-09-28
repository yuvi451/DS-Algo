class MinHeap:
    def __init__(self, arr = None):
        self.heap = []
        if type(arr) is list:
            self.heap = arr.copy()
            for i in range(len(self.heap) - 1, -1, -1):
                self._shift_down(i)

    def _shift_up(self, i):
        parent = (i - 1)//2
        while i != 0 and self.heap[i] < self.heap[parent]:
            self.heap[i], self.heap[parent] = self.heap[parent], self.heap[i]
            i = parent
            parent = (i - 1)//2

    def _shift_down(self, i):
        left = 2*i + 1
        right = 2*i + 2
        while (left < len(self.heap) and self.heap[i] > self.heap[left]) or (right < len(self.heap) and self.heap[i] > self.heap[right]):
            smallest = left if (right >= len(self.heap) or self.heap[left] < self.heap[right]) else right
            self.heap[i], self.heap[smallest] = self.heap[smallest], self.heap[i]
            i = smallest
            left = 2*i + 1
            right = 2*i + 2

    def insert(self, element):
        self.heap.append(element)
        self._shift_up(len(self.heap) - 1)

    def get_min(self):
        return self.heap[0] if len(self.heap) > 0 else None

    def extract_min(self):
        if len(self.heap) == 0:
            return None
        min_val = self.heap[0]
        self.heap[0], self.heap[-1] = self.heap[-1], self.heap[0]
        self.heap.pop()
        self._shift_down(0)
        return min_val

    def update_by_index(self, i , new):
        old = self.heap[i]
        self.heap[i] = new
        if new < old:
            self._shift_up(i)
        else:
            self._shift_down(i)

    def update(self, old, new):
        if old in self.heap:
            self.update_by_index(self.heap.index(old), new)

class MaxHeap:
    def __init__(self, arr = None):
        self.heap = []
        if type(arr) is list:
            self.heap = arr.copy()
            for i in range(len(self.heap) - 1, -1, -1):
                self._shift_down(i)

    def _shift_up(self, i):
        parent = (i-1)//2
        while i != 0 and self.heap[i] > self.heap[parent]:
            self.heap[i], self.heap[parent] = self.heap[parent], self.heap[i]
            i = parent
            parent = (i-1)//2

    def _shift_down(self, i):
        left = 2*i + 1
        right = 2*i + 2
        while (left < len(self.heap) and self.heap[i] < self.heap[left]) or (right < len(self.heap) and self.heap[i] < self.heap[right]):
            biggest = left if (right >= len(self.heap) or self.heap[left] > self.heap[right]) else right
            self.heap[i], self.heap[biggest] = self.heap[biggest], self.heap[i]
            i = biggest
            left = 2*i + 1
            right = 2*i + 2

    def insert(self, element):
        self.heap.append(element)
        self._shift_up(len(self.heap)-1)

    def get_max(self):
        return self.heap[0] if len(self.heap) > 0 else None

    def extract_max(self):
        if len(self.heap) == 0:
            return None
        max_val = self.heap[0]
        self.heap[0], self.heap[-1] = self.heap[-1], self.heap[0]
        self.heap.pop()
        self._shift_down(0)
        return max_val

    def update_by_index(self, i, new):
        old = self.heap[i]
        self.heap[i] = new
        if new > old:
            self._shift_up(i)
        else:
            self._shift_down(i)

    def update(self, old, new):
        if old in self.heap:
            self.update_by_index(self.heap.index(old), new)

def heapsort(arr):
    heap = MinHeap(arr)
    return [heap.extract_min() for i in range(len(heap.heap))]


class PriorityQueue:
    def __init__(self):
        self.queue = MaxHeap()

    def enqueue(self, element):
        self.queue.insert(element)

    def peek(self):
        return self.queue.get_max()

    def dequeue(self, element):
        return self.queue.extract_max()

    def is_empty(self):
        return len(self.queue.heap) == 0

    def change_priority_by_index(self, i, new):
        self.queue.update_by_index(i, new)

    def change_priority(self, old, new):
        self.queue.update(old, new)
