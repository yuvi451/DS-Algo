from heap import *
from treasure import *

def max_heap(a, b):
    if a.priority() > b.priority() or (a.priority() == b.priority() and a.id < b.id):
        return True
    return False

class CrewMate:

    def __init__(self, id):
        self.id = id
        self.treasures = []
        self.l = []
        self.load = 0
        self.last_load_time = 0
        self.prev_time = 0
        self.heap_t = Heap(max_heap, [])

    def process(self, hp, curr_time, prev_time, l):
        while hp.top() and prev_time < curr_time:
            a = hp.extract()
            if prev_time + a.remaining_size() <= curr_time:
                prev_time += a.remaining_size()
                a.completion_time = prev_time
                l.append(a)
            else:
                a.processed_time += (curr_time - prev_time)
                prev_time = curr_time
                hp.insert(a)


    def add_t(self, trsr):
        self.treasures.append(trsr)

    def get_compltn_time(self):
        for i in self.treasures:
            self.process(self.heap_t, i.arrival_time, self.prev_time, self.l)
            self.heap_t.insert(i)
            self.prev_time = i.arrival_time

        d = []
        prev_time1 = self.prev_time
        for i in self.heap_t.heap:
            i = i.copy()
            i.completion_time = i.remaining_size() + prev_time1
            d.append(i)
            prev_time1 = i.completion_time

        self.treasures.clear()
        return self.l + d











