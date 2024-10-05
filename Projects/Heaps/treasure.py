class Treasure:

    def __init__(self, id, size, arrival_time):
        self.id = id
        self.size = size
        self.arrival_time = arrival_time
        self.completion_time = 0
        self.processed_time = 0
        self.person_id = None

    def remaining_size(self):
        return self.size - self.processed_time

    def priority(self):
        return - self.arrival_time - self.remaining_size()

    def copy(self):
        new_treasure = Treasure(self.id, self.size, self.arrival_time)
        new_treasure.completion_time = self.completion_time
        new_treasure.processed_time = self.processed_time
        return new_treasure
