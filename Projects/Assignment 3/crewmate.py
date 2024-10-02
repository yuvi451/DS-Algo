from heap import *
from treasure import *

def max_heap(a, b):
    if a.priority() > b.priority():
        return True
    elif a.priority() < b.priority():
        return False
    else:
        if a.id < b.id:
            return True
        else:
            return False


class CrewMate:

    def __init__(self):
        self.heap_t = Heap(max_heap, [])
        self.load = 0
        self.processed_objects = []
        self.time = [0]

    def process_t(self, t):

        # All elements are processed upto arrival time of last element

        a = self.heap_t.top()
        time = self.time[-1]
        while a is not None:
            b = self.heap_t.extract()
            if time + b.remaining_size() <= t:
                time += b.remaining_size()
                b.completion_time = time
                self.processed_objects.append(b)
            else:
                b.processed_time += (t - time)
                time = t
                self.heap_t.insert(b)
                break
            a = self.heap_t.top()

        self.time.append(t)

    def add_t(self, treasure):
        self.process_t(treasure.arrival_time)
        self.heap_t.insert(treasure)
        self.load += treasure.remaining_size()
        self.time.append(treasure.arrival_time)


    def get_cmpltn_time(self):
        b = self.heap_t.top()
        t = self.time[-1]
        a = []
        while b is not None:
            b = self.heap_t.extract()
            b.completion_time = t + b.remaining_size()
            t = b.completion_time
            a.append(b)
            b = self.heap_t.top()
        for i in a:
            self.heap_t.insert(i)
        return self.processed_objects + [t for t in self.heap_t.heap]
