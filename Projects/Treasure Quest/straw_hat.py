from crewmate import CrewMate
from heap import Heap
from treasure import Treasure

def comp(C1, C2):
    # here crewmate C1 received the latest treasure and is being inserted back into the heap
    # current time = C1.last_load_time = arrival time of latest treasure
    # C1's load is updated at current time but C2's load is not so...
    p1 = C1.load
    t = C2.load - (C1.last_load_time - C2.last_load_time)
    p2 = t if t > 0 else 0  # load of crewmate C2 at current time

    if p1 <= p2: return True
    return False

class StrawHatTreasury:

    def __init__(self, m):
        self.all_crewmates = [CrewMate(i) for i in range(1, m + 1)]
        self.crewmate_heap = Heap(comp, self.all_crewmates)

    def add_treasure(self, treasure):
        crewmate = self.crewmate_heap.extract()
        crewmate.add(treasure)
        self.crewmate_heap.insert(crewmate)

    def copy(self, T):
        return Treasure(T.id, T.size, T.arrival_time)

    def get_completion_time(self):
       a = []
       for crewmate in self.crewmate_heap.heap:
           a.extend(crewmate.processed_treasures)

           last_load_time = crewmate.last_load_time
           for treasure in crewmate.pq.heap:
               T = self.copy(treasure)
               T.completion_time = last_load_time + T.remaining_size()
               a.append(T)
               last_load_time += T.remaining_size()

       return sorted(a, key=lambda x: x.id)
