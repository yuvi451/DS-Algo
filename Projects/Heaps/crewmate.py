from heap import Heap
from treasure import Treasure

def comp(T1, T2):
    p1 = -(T1.arrival_time + T1.remaining_size())
    p2 = -(T2.arrival_time + T2.remaining_size())

    if p1 > p2 or (p1 == p2 and T1.id < T2.id): return True
    return False

class CrewMate:

    def __init__(self, crew_id):
        self.crew_id = crew_id
        self.load = 0
        self.last_load_time = 0
        self.pq = Heap(comp, [])    # All treasures in pq of crewmate are processed upto last_load_time of crewmate
        self.processed_treasures = []

    def add(self, T):
        curr_time = T.arrival_time
        processing_units = curr_time - self.last_load_time
        t = self.last_load_time

        while self.pq.top() is not None and processing_units > 0:
            Tr_top = self.pq.extract()

            if processing_units >= Tr_top.remaining_size():
                processing_units -= (Tr_top.remaining_size())
                self.load -= (Tr_top.remaining_size())
                t += (Tr_top.remaining_size())
                Tr_top.completion_time = t
                Tr_top.size = 0
                self.processed_treasures.append(Tr_top)

            else:
                Tr_top.size -= processing_units
                self.load -= processing_units
                processing_units = 0
                self.pq.insert(Tr_top)

        self.last_load_time = T.arrival_time
        self.pq.insert(T)
        self.load += T.size
