from crewmate import *
from heap import *


def min_heap(a, b):
    if a.load < b.load:
        return True
    else:
        return False


class StrawHatTreasury:

    def __init__(self, m):
        self.crew = [CrewMate() for i in range(m)]
        self.heap_c = Heap(min_heap, self.crew)
        self.time = [0]
        self.all_treasures = []

    def process_load(self, t):
        if self.heap_c.top() is None:
            return None

        temp_list = []
        while self.heap_c.top() is not None:
            b = self.heap_c.extract()
            b.load = max(0, b.load - (t - self.time[-1]))
            temp_list.append(b)

        for obj in temp_list:
            self.heap_c.insert(obj)

        self.time.append(t)

    def add_treasure(self, treasure):
        self.process_load(treasure.arrival_time)
        person = self.heap_c.extract()
        if person:
            person.add_t(treasure)
            self.heap_c.insert(person)
        self.all_treasures.append(treasure)

    # def get_completion_time(self):
    #     l = []
    #     a = self.heap_c.extract()
    #     while a is not None:
    #         b = a.get_cmpltn_time()
    #         for i in b:
    #             l.append(i)
    #         a = self.heap_c.extract()
    #     l.sort(key= lambda x : x.id)
    #     return l

    def get_completion_time(self):
        # Process all treasures up to the latest arrival time
        if self.all_treasures:
            latest_time = max(t.arrival_time for t in self.all_treasures)
            self.process_load(latest_time)

        # Get completion times from all crew members
        all_processed = []
        temp_crew = []
        while self.heap_c.top() is not None:
            crew_member = self.heap_c.extract()
            all_processed.extend(crew_member.get_cmpltn_time())
            temp_crew.append(crew_member)

        # Restore the heap
        for crew_member in temp_crew:
            self.heap_c.insert(crew_member)

        # Sort by treasure ID and return
        return sorted(all_processed, key=lambda x: x.id)

# r = StrawHatTreasury(3)
# t1 = Treasure(1, 2, 1)
# t2 = Treasure(2, 6, 2)
# t3 = Treasure(3, 4, 3)
# t4 = Treasure(4, 2, 4)
# t5 = Treasure(5, 8, 7)
# t6 = Treasure(6, 1, 9)
# t7 = Treasure(7, 4, 13)
# t8 = Treasure(8, 3, 20)
# r.add_treasure(t1)
# r.add_treasure(t2)
# r.add_treasure(t3)
# r.add_treasure(t4)
# # r.add_treasure(t5)
# # r.add_treasure(t6)
# # r.add_treasure(t7)
# # r.add_treasure(t8)
#
#
# a = r.heap_c.top()
# while a is not None:
#     b = r.heap_c.extract()
#     print(b.load)
#     a = r.heap_c.top()

# print(r.crew)

