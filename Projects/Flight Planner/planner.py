from flight import Flight

class MinHeap:
    def __init__(self, arr=None):
        self.heap = []
        if type(arr) is list:
            self.heap = arr.copy()
            for i in range(len(self.heap) - 1, -1, -1):
                self._shift_down(i)

    def _shift_up(self, i):
        parent = (i - 1) // 2
        while i != 0 and self.heap[i] < self.heap[parent]:
            self.heap[i], self.heap[parent] = self.heap[parent], self.heap[i]
            i = parent
            parent = (i - 1) // 2

    def _shift_down(self, i):
        left = 2 * i + 1
        right = 2 * i + 2
        while (left < len(self.heap) and self.heap[i] > self.heap[left]) or (
                right < len(self.heap) and self.heap[i] > self.heap[right]):
            smallest = left if (right >= len(self.heap) or self.heap[left] < self.heap[right]) else right
            self.heap[i], self.heap[smallest] = self.heap[smallest], self.heap[i]
            i = smallest
            left = 2 * i + 1
            right = 2 * i + 2

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


class PriorityQueue:
    def __init__(self):
        self.queue = MinHeap()

    def push(self, element):
        self.queue.insert(element)

    def top(self):
        return self.queue.get_min()

    def pop(self):
        return self.queue.extract_min()

    def is_empty(self):
        return len(self.queue.heap) == 0


class Graph:
    def __init__(self, m):
        self.adj = [[] for i in range(m + 1)]

    def addEdge(self, f1, f2):
        self.adj[f1.flight_no].append(f2)


class Planner:
    def __init__(self, flights):
        self.m = len(flights)
        self.all_flights = [None for i in range(self.m + 1)]
        self.start_city = [[] for i in range(self.m + 1)]
        self.end_city = [[] for i in range(self.m + 1)]
        self.graph = Graph(self.m)

        for i in flights:
            self.all_flights[i.flight_no] = i
            self.start_city[i.start_city].append(i)
            self.end_city[i.end_city].append(i)

        for i in flights:
            end_i = i.end_city
            for j in self.start_city[end_i]:
                if j.departure_time - i.arrival_time >= 20:
                    self.graph.addEdge(i, j)

    def least_flights_ealiest_route(self, start_city, end_city, t1, t2):
        list = [(1e9, 1e9, None) for i in range(self.m + 1)]  # (distance, t_arrival, parent)
        route = []

        if start_city != end_city and t1 <= t2:
            for i in self.start_city[start_city]:
                if i.departure_time >= t1 and i.arrival_time <= t2:
                    list[i.flight_no] = (0, i.arrival_time, None)
                    visited = [False] * (self.m + 1)
                    visited[i.flight_no] = True
                    q = [i]

                    while q:
                        flight = q.pop(0)

                        for next_flight in self.graph.adj[flight.flight_no]:
                            if next_flight.arrival_time <= t2 and not visited[next_flight.flight_no]:
                                visited[next_flight.flight_no] = True
                                q.append(next_flight)

                                flt = list[next_flight.flight_no]
                                par = list[flight.flight_no]
                                if par[0] + 1 < flt[0]:
                                    list[next_flight.flight_no] = (1 + par[0], next_flight.arrival_time, flight)

            last_flight = (1e9, 1e9, None)
            flt = None
            for i in self.end_city[end_city]:
                ft = list[i.flight_no]
                if ft[0] < last_flight[0]:
                    last_flight = ft
                    flt = i
                elif ft[0] == last_flight[0] and ft[1] < last_flight[1]:
                    last_flight = ft
                    flt = i

            if flt is not None:
                route.append(flt)
                while last_flight[2] is not None:
                    route.append(last_flight[2])

                    last_flight = list[last_flight[2].flight_no]

        return route[::-1]

    def cheapest_route(self, start_city, end_city, t1, t2):
        route = []
        list = [(1e9, None) for i in range(self.m + 1)]   # (cost, parent)

        if start_city != end_city and t1 <= t2:
            for i in self.start_city[start_city]:
                if i.departure_time >= t1 and i.arrival_time <= t2:
                    list[i.flight_no] = (i.fare, None)
                    visited = [False] * (self.m + 1)
                    pq = PriorityQueue()
                    pq.push((i.fare, i.flight_no))

                    while not pq.is_empty():
                        flight = pq.pop()

                        if not visited[flight[1]]:
                            visited[flight[1]] = True
                            for next_flight in self.graph.adj[flight[1]]:
                                if next_flight.arrival_time <= t2:
                                    flt = list[next_flight.flight_no]
                                    par = list[flight[1]]

                                    if par[0] + next_flight.fare < flt[0]:
                                        list[next_flight.flight_no] = (par[0] + next_flight.fare, self.all_flights[flight[1]])
                                        pq.push((par[0] + next_flight.fare, next_flight.flight_no))

            last_flight = (1e9, None)
            flt = None
            for i in self.end_city[end_city]:
                ft = list[i.flight_no]
                if ft[0] < last_flight[0]:
                    last_flight = ft
                    flt = i

            if flt is not None:
                route.append(flt)
                while last_flight[1] is not None:
                    route.append(last_flight[1])

                    last_flight = list[last_flight[1].flight_no]

        return route[::-1]

    def least_flights_cheapest_route(self, start_city, end_city, t1, t2):
        route = []
        list = [(1e9, 1e9, None) for i in range(self.m + 1)]   # (distance, cost, parent)

        if start_city != end_city and t1 <= t2:
            for i in self.start_city[start_city]:
                if i.departure_time >= t1 and i.arrival_time <= t2:
                    list[i.flight_no] = (0, i.fare, None)
                    visited = [False] * (self.m + 1)
                    pq = PriorityQueue()
                    pq.push((0, i.fare, i.flight_no))

                    while not pq.is_empty():
                        flight = pq.pop()

                        if not visited[flight[2]]:
                            visited[flight[2]] = True
                            for next_flight in self.graph.adj[flight[2]]:
                                if next_flight.arrival_time <= t2:
                                    flt = list[next_flight.flight_no]
                                    par = list[flight[2]]

                                    if par[0] + 1 < flt[0]:
                                        list[next_flight.flight_no] = (par[0] + 1, par[1] + next_flight.fare, self.all_flights[flight[2]])
                                        pq.push((par[0] + 1, par[1] + next_flight.fare, next_flight.flight_no))

                                    elif par[0] + 1 == flt[0] and par[1] + next_flight.fare < flt[1]:
                                        list[next_flight.flight_no] = (flt[0], par[1] + next_flight.fare, self.all_flights[flight[2]])
                                        pq.push((flt[0], par[1] + next_flight.fare, next_flight.flight_no))

            last_flight = (1e9, 1e9, None)
            flt = None
            for i in self.end_city[end_city]:
                ft = list[i.flight_no]
                if ft[0] < last_flight[0]:
                    last_flight = ft
                    flt = i
                elif ft[0] == last_flight[0] and ft[1] < last_flight[1]:
                    last_flight = ft
                    flt = i

            if flt is not None:
                route.append(flt)
                while last_flight[2] is not None:
                    route.append(last_flight[2])

                    last_flight = list[last_flight[2].flight_no]

        return route[::-1]
