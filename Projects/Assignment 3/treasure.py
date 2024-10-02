class Treasure:

    def __init__(self, id, size, arrival_time):
        self.id = id
        self.size = size
        self.arrival_time = arrival_time
        self.completion_time = 0
        self.processed_time = 0

    def remaining_size(self):
        return self.size - self.processed_time

    def priority(self):
        return - self.arrival_time - self.remaining_size()