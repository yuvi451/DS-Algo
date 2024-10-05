from crewmate import *
from treasure import *

def min_heap(a, b):
    if a.load < b.load:
        return True
    return False

class StrawHatTreasury:

    def __init__(self, m):
        self.all_crewmates = [0]*(m + 1)
        self.crew = [CrewMate(i) for i in range(1, m + 1)]
        self.heap_c = Heap(min_heap, self.crew)
        self.crewmates_to_process = []
    def add_treasure(self, trsr):
        person = self.heap_c.extract_1(trsr.arrival_time)
        if person:
            if self.all_crewmates[person.id] == 0:
                self.all_crewmates[person.id] = 1
                self.crewmates_to_process.append(person)
            person.add_t(trsr)
            person.load = max(0, person.load - (trsr.arrival_time - person.last_load_time))
            person.load += trsr.size
            person.last_load_time = trsr.arrival_time
            self.heap_c.insert_1(person, trsr.arrival_time)

    def get_completion_time(self):
        a = []
        for i in self.crewmates_to_process:
            a.extend(i.get_compltn_time())
        return sorted(a, key=lambda x:x.id)







