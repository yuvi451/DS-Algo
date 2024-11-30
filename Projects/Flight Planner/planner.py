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
    def __init__(self, nodes):
        self.nodes = nodes
        self.adj = [[] for i in range(nodes + 1)]

    def addEdge(self, a, b):
        self.adj[a].append(b)


class Planner:
    def __init__(self, flights):
        self.m = len(flights)
        self.graph = Graph(self.m)
        self.city_start, self.city_end, self.all_flights = [None] * (self.m + 1), [None] * (self.m + 1), [None] * (self.m + 1)

        for flt in flights:
            start_city = flt.start_city
            end_city = flt.end_city

            if self.city_start[start_city] is None:
                self.city_start[start_city] = [flt]
            else:
                self.city_start[start_city].append(flt)

            if self.city_end[end_city] is None:
                self.city_end[end_city] = [flt]
            else:
                self.city_end[end_city].append(flt)

            self.all_flights[flt.flight_no] = flt

        for flight1 in self.all_flights:
            if flight1:
                end_city = flight1.end_city
                atime = flight1.arrival_time
                if self.city_start[end_city] is not None:
                    for flight2 in self.city_start[end_city]:
                        dtime = flight2.departure_time
                        if dtime - atime >= 20:
                            self.graph.addEdge(flight1.flight_no, flight2.flight_no)

    def least_flights_ealiest_route(self, start_city, end_city, t1, t2):
        path = []

        if self.city_start[start_city] is not None and start_city != end_city:
            for flt in self.city_start[start_city]:
                if flt.departure_time >= t1 and flt.arrival_time <= t2:
                    visited, distance = [False] * (self.m + 1), [(0, 0)] * (self.m + 1)    # (distance, previous_flight_object)
                    visited[flt.flight_no] = True
                    q = [flt.flight_no]

                    while q:
                        curr_flight = q.pop(0)

                        for flight in self.graph.adj[curr_flight]:
                            next_flight_obj = self.all_flights[flight]
                            next_flight_no = flight
                            if not visited[next_flight_no] and next_flight_obj.departure_time >= t1 and next_flight_obj.arrival_time <= t2:
                                visited[next_flight_no] = True
                                q.append(next_flight_no)
                                distance[next_flight_no] = (distance[curr_flight][0] + 1, self.all_flights[curr_flight])

                    t = (None, 1e9, 1e9)       # (flight_object, distance, time)
                    if self.city_end[end_city]:
                        for flgt in self.city_end[end_city]:
                            if flgt.departure_time >= t1 and flgt.arrival_time <= t2:
                                if distance[flgt.flight_no][1]:
                                    if distance[flgt.flight_no][0] < t[1]:
                                        t = (flgt, distance[flgt.flight_no][0], flgt.arrival_time)
                                    elif distance[flgt.flight_no][0] == t[1] and flgt.arrival_time < t[2]:
                                        t = (flgt, distance[flgt.flight_no][0], flgt.arrival_time)
                                elif distance[flgt.flight_no][1] == 0 and flgt.start_city == start_city and flgt.arrival_time < t[2]:
                                    t = (flgt, distance[flgt.flight_no][0], flgt.arrival_time)

                    if t[0] is not None:
                        curr_path = []
                        curr_flgt = t[0]
                        while distance[curr_flgt.flight_no][1] != 0:
                            curr_path.append(curr_flgt)
                            curr_flgt = distance[curr_flgt.flight_no][1]
                        curr_path.append(curr_flgt)

                        curr_path.reverse()
                        if (len(path) == 0) or (len(curr_path) < len(path)) or (len(path) == len(curr_path) and curr_path[-1].arrival_time < path[-1].arrival_time):
                            path = curr_path
        return path

    def cheapest_route(self, start_city, end_city, t1, t2):
        path = []

        if self.city_start[start_city] is not None and start_city != end_city:
            for flt in self.city_start[start_city]:
                if flt.departure_time >= t1 and flt.arrival_time <= t2:
                    cost, processed = [(1e9, 1e9)] * (self.m + 1), [False] * (self.m + 1)
                    pq = PriorityQueue()
                    cost[flt.flight_no] = (0, 0)
                    pq.push((0, flt.flight_no))

                    while not pq.is_empty():
                        curr_flight = pq.top()[1]
                        pq.pop()

                        if processed[curr_flight]: continue
                        processed[curr_flight] = True

                        for flight in self.graph.adj[curr_flight]:
                            next_flight_obj = self.all_flights[flight]
                            next_flight_no = flight
                            if next_flight_obj.departure_time >= t1 and next_flight_obj.arrival_time <= t2 and cost[next_flight_no][0] > cost[curr_flight][0] + next_flight_obj.fare:
                                cost[next_flight_no] = (cost[curr_flight][0] + next_flight_obj.fare, self.all_flights[curr_flight])
                                pq.push((cost[next_flight_no][0], next_flight_no))

                    a = (1e9, None)      # (cost, flight_object)
                    if self.city_end[end_city]:
                        for flgts in self.city_end[end_city]:
                            if flgts.departure_time >= t1 and flgts.arrival_time <= t2:
                                if cost[flgts.flight_no][0] < a[0]:
                                    a = (cost[flgts.flight_no][0], flgts)

                    if a[1] is not None:
                        curr_path = []
                        curr_flgt = a[1]
                        while cost[curr_flgt.flight_no][1] != 0:
                            curr_path.append(curr_flgt)
                            curr_flgt = cost[curr_flgt.flight_no][1]
                        curr_path.append(curr_flgt)

                        curr_path.reverse()
                        cst1, cst2 = 0, 0
                        for i in curr_path: cst1 += i.fare
                        for i in path: cst2 += i.fare
                        if cst2 == 0 or cst2 > cst1:
                            path = curr_path
        return path
    def least_flights_cheapest_route(self, start_city, end_city, t1, t2):
        path = []

        if self.city_start[start_city] is not None and start_city != end_city:
            for flt in self.city_start[start_city]:
                if flt.departure_time >= t1 and flt.arrival_time <= t2:
                    visited, distance = [False] * (self.m + 1), [(0, 0)] * (self.m + 1)  # (distance, previous_flight_object)
                    visited[flt.flight_no] = True
                    q = [flt.flight_no]

                    while q:
                        curr_flight = q.pop(0)

                        for flight in self.graph.adj[curr_flight]:
                            next_flight_obj = self.all_flights[flight]
                            next_flight_no = flight
                            if not visited[next_flight_no] and next_flight_obj.departure_time >= t1 and next_flight_obj.arrival_time <= t2:
                                visited[next_flight_no] = True
                                q.append(next_flight_no)
                                distance[next_flight_no] = (distance[curr_flight][0] + 1, self.all_flights[curr_flight])

                    cost, processed = [(1e9, None)] * (self.m + 1), [False] * (self.m + 1)
                    pq = PriorityQueue()
                    cost[flt.flight_no] = (0, None)
                    pq.push((0, flt.flight_no))

                    while not pq.is_empty():
                        curr_flight = pq.top()[1]
                        pq.pop()

                        if processed[curr_flight]: continue
                        processed[curr_flight] = True

                        for flight in self.graph.adj[curr_flight]:
                            next_flight_obj = self.all_flights[flight]
                            next_flight_no = flight
                            if next_flight_obj.departure_time >= t1 and next_flight_obj.arrival_time <= t2 and cost[next_flight_no][0] > cost[curr_flight][0] + next_flight_obj.fare and (distance[next_flight_no][0] - distance[curr_flight][0] == 1):
                                cost[next_flight_no] = (cost[curr_flight][0] + next_flight_obj.fare, self.all_flights[curr_flight])
                                pq.push((cost[next_flight_no][0], next_flight_no))

                    a = (1e9, 1e9, None)  # (distance, cost, flight_object)
                    if self.city_end[end_city]:
                        for flgts in self.city_end[end_city]:
                            if flgts.departure_time >= t1 and flgts.arrival_time:
                                if distance[flgts.flight_no][1]:
                                    if distance[flgts.flight_no][0] < a[0]:
                                        a = (distance[flgts.flight_no][0], cost[flgts.flight_no][0], flgts)
                                    elif distance[flgts.flight_no][0] == a[0] and cost[flgts.flight_no][0] < a[1]:
                                        a = (distance[flgts.flight_no][0], cost[flgts.flight_no][0], flgts)
                                elif distance[flgts.flight_no][1] == 0 and flgts.start_city == start_city and cost[flgts.flight_no][0] < a[1]:
                                    a = (distance[flgts.flight_no][0], cost[flgts.flight_no][0], flgts)

                    if a[2] is not None:
                        curr_path = []
                        curr_flgt = a[2]
                        while curr_flgt is not None:
                            curr_path.append(curr_flgt)
                            curr_flgt = cost[curr_flgt.flight_no][1]

                        curr_path.reverse()
                        cst1, cst2 = 0, 0
                        for i in curr_path: cst1 += i.fare
                        for i in path: cst2 += i.fare
                        if (len(path) == 0) or len(curr_path) < len(path) or (len(path) == len(curr_path) and cst1 < cst2):
                            path = curr_path
        return path