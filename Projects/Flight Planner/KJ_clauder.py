from typing import List, Tuple, Set, NamedTuple
from collections import defaultdict, deque
from dataclasses import dataclass
from flight import Flight
from planner import Planner


@dataclass(frozen=True)
class Route:
    """Immutable route representation for caching and comparison"""
    flights: Tuple[Flight, ...]

    @property
    def total_fare(self) -> int:
        return sum(f.fare for f in self.flights)

    @property
    def arrival_time(self) -> int:
        return self.flights[-1].arrival_time if self.flights else float('inf')

    @property
    def departure_time(self) -> int:
        return self.flights[0].departure_time if self.flights else float('inf')

    @property
    def num_flights(self) -> int:
        return len(self.flights)


class TestCase(NamedTuple):
    """Test case structure"""
    name: str
    description: str
    start_city: int
    end_city: int
    time_start: int
    time_end: int


class RobustFlightChecker:
    """A comprehensive checker for flight route validation"""

    def __init__(self, flights: List[Flight]):
        self.flights = flights
        self.flight_graph = defaultdict(list)
        self._build_flight_graph()
        self._validate_city_limit()

    def _build_flight_graph(self):
        """Build an optimized graph representation of flights"""
        for flight in self.flights:
            self.flight_graph[flight.start_city].append(flight)
        for city_flights in self.flight_graph.values():
            city_flights.sort(key=lambda f: f.departure_time)

    def _validate_city_limit(self):
        """Validate that no city has more than 100 flights"""
        city_flight_counts = defaultdict(int)
        for flight in self.flights:
            city_flight_counts[flight.start_city] += 1
            city_flight_counts[flight.end_city] += 1
        for city, count in city_flight_counts.items():
            if count > 100:
                raise ValueError(f"City {city} has {count} flights, exceeding limit of 100")

    def is_valid_connection(self, flight1: Flight, flight2: Flight) -> bool:
        """Verify if two flights can be connected with required buffer time"""
        return (flight1.end_city == flight2.start_city and
                flight2.departure_time >= flight1.arrival_time + 20)

    def is_valid_route(self, route: Route, t1: int, t2: int) -> bool:
        """Comprehensively validate a route against all constraints"""
        # Special case: start city = end city
        if not route.flights:
            return True  # An empty route is valid when start = end

        if route.departure_time < t1 or route.arrival_time > t2:
            return False
        for i in range(len(route.flights) - 1):
            if not self.is_valid_connection(route.flights[i], route.flights[i + 1]):
                return False
        return True

    def validate_least_flights_earliest(self, route: Route, all_routes: Set[Route]) -> bool:
        """Validate route has minimum flights and earliest arrival among min-flight routes"""
        if not all_routes:
            return not route.flights  # True if route is empty, False otherwise
        min_flights = min(r.num_flights for r in all_routes)
        if route.num_flights != min_flights:
            return False
        min_flight_routes = {r for r in all_routes if r.num_flights == min_flights}
        earliest_arrival = min(r.arrival_time for r in min_flight_routes)
        return route.arrival_time == earliest_arrival

    def validate_cheapest(self, route: Route, all_routes: Set[Route]) -> bool:
        """Validate route has minimum total fare"""
        if not all_routes:
            return not route.flights  # True if route is empty, False otherwise
        min_fare = min(r.total_fare for r in all_routes)
        if route.total_fare != min_fare:
            print(route.total_fare, min_fare)
            exit(1)
        return route.total_fare == min_fare

    def validate_least_flights_cheapest(self, route: Route, all_routes: Set[Route]) -> bool:
        """Validate route has minimum flights and is cheapest among min-flight routes"""
        if not all_routes:
            return not route.flights  # True if route is empty, False otherwise
        min_flights = min(r.num_flights for r in all_routes)
        if route.num_flights != min_flights:
            return False
        min_flight_routes = {r for r in all_routes if r.num_flights == min_flights}
        min_fare = min(r.total_fare for r in min_flight_routes)
        if route.total_fare != min_fare:
            print(route.total_fare, min_fare)
            exit(1)
        return route.total_fare == min_fare


def run_comprehensive_tests(planner_class, flights: List[Flight], test_cases: List[TestCase]):
    """Run all test cases and provide detailed results"""
    checker = RobustFlightChecker(flights)

    print("\n=== Comprehensive Flight Planner Testing ===")
    total_tests = len(test_cases)
    passed_tests = 0

    def format_route(route):
        return [(f.flight_no, f.start_city, f.departure_time, f.end_city,
                 f.arrival_time, f.fare) for f in route.flights]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case.name}")
        print(f"Description: {test_case.description}")

        try:
            planner = planner_class(flights)

            # Check if start city and end city are the same
            if test_case.start_city == test_case.end_city:
                print("Expected: No valid routes (start city = end city)")
                route1 = planner.least_flights_ealiest_route(
                    test_case.start_city, test_case.end_city,
                    test_case.time_start, test_case.time_end
                )
                route2 = planner.cheapest_route(
                    test_case.start_city, test_case.end_city,
                    test_case.time_start, test_case.time_end
                )
                route3 = planner.least_flights_cheapest_route(
                    test_case.start_city, test_case.end_city,
                    test_case.time_start, test_case.time_end
                )
                print(f"Got:      {format_route(Route(tuple(route1 or [])))}")
                print(f"Got:      {format_route(Route(tuple(route2 or [])))}")
                print(f"Got:      {format_route(Route(tuple(route3 or [])))}")

                if any([route1, route2, route3]):
                    print("❌ Test case failed: Planner returned route when no valid routes exist")
                else:
                    print("✅ Test case passed: Correctly handled case with start = end city")
                    passed_tests += 1
                continue

            all_routes = checker.find_all_valid_routes(
                test_case.start_city,
                test_case.end_city,
                test_case.time_start,
                test_case.time_end
            )

            if not all_routes:
                print("Expected: No valid routes")
                route1 = planner.least_flights_ealiest_route(
                    test_case.start_city, test_case.end_city,
                    test_case.time_start, test_case.time_end
                )
                route2 = planner.cheapest_route(
                    test_case.start_city, test_case.end_city,
                    test_case.time_start, test_case.time_end
                )
                route3 = planner.least_flights_cheapest_route(
                    test_case.start_city, test_case.end_city,
                    test_case.time_start, test_case.time_end
                )
                print(f"Got:      {format_route(Route(tuple(route1 or [])))}")
                print(f"Got:      {format_route(Route(tuple(route2 or [])))}")
                print(f"Got:      {format_route(Route(tuple(route3 or [])))}")

                if any([route1, route2, route3]):
                    print("❌ Test case failed: Planner returned route when no valid routes exist")
                else:
                    print("✅ Test case passed: Correctly handled case with no valid routes")
                    passed_tests += 1
                continue

            route1 = Route(tuple(planner.least_flights_ealiest_route(
                test_case.start_city, test_case.end_city,
                test_case.time_start, test_case.time_end
            ) or []))
            route2 = Route(tuple(planner.cheapest_route(
                test_case.start_city, test_case.end_city,
                test_case.time_start, test_case.time_end
            ) or []))
            route3 = Route(tuple(planner.least_flights_cheapest_route(
                test_case.start_city, test_case.end_city,
                test_case.time_start, test_case.time_end
            ) or []))

            validations = []

            expected_route1 = min((r for r in all_routes if r.num_flights == min(r.num_flights for r in all_routes)),
                                  key=lambda r: r.arrival_time)
            expected_route2 = min(all_routes, key=lambda r: r.total_fare)
            min_flights = min(r.num_flights for r in all_routes)
            expected_route3 = min((r for r in all_routes if r.num_flights == min_flights), key=lambda r: r.total_fare)

            if not checker.is_valid_route(route1, test_case.time_start, test_case.time_end):
                validations.append("Route 1 violates basic constraints")
            elif not checker.validate_least_flights_earliest(route1, all_routes):
                validations.append("Route 1 is not optimal for least flights and earliest arrival")

            if not checker.is_valid_route(route2, test_case.time_start, test_case.time_end):
                validations.append("Route 2 violates basic constraints")
            elif not checker.validate_cheapest(route2, all_routes):
                validations.append("Route 2 is not the cheapest possible route")

            if not checker.is_valid_route(route3, test_case.time_start, test_case.time_end):
                validations.append("Route 3 violates basic constraints")
            elif not checker.validate_least_flights_cheapest(route3, all_routes):
                validations.append("Route 3 is not optimal for least flights and cheapest")

            if validations:
                print("\n❌ Test case failed:")
                print("Task 1: Least Flights and Earliest Route:")
                print(f"Expected: {format_route(expected_route1)}")
                print(f"Got:      {format_route(route1)}")
                print("\nTask 2: Cheapest Route:")
                print(f"Expected: {format_route(expected_route2)}")
                print(f"Got:      {format_route(route2)}")
                print("\nTask 3: Least Flights and Cheapest Route:")
                print(f"Expected: {format_route(expected_route3)}")
                print(f"Got:      {format_route(route3)}")
                for validation in validations:
                    print(f"  - {validation}")
            else:
                print("\n✅ Test case passed: All routes are valid and optimal")
                passed_tests += 1

        except Exception as e:
            print(f"❌ Test case failed: Error during test execution: {str(e)}")

    print(f"\n=== Test Summary ===")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    # Sample test flights
    flights = [
        Flight(0, 0, 100, 1, 200, 50),
        Flight(1, 1, 250, 2, 350, 60),
        Flight(2, 2, 400, 3, 500, 70),
        Flight(3, 3, 550, 4, 650, 80),
        Flight(4, 0, 100, 4, 300, 500),
        Flight(5, 0, 100, 3, 250, 400),
        Flight(6, 0, 100, 2, 200, 40),
        Flight(7, 2, 220, 4, 350, 45),
        Flight(8, 1, 220, 3, 320, 35),
        Flight(9, 3, 340, 4, 440, 30),
        Flight(10, 0, 150, 5, 250, 55),
        Flight(11, 5, 270, 3, 370, 45),
        Flight(12, 5, 270, 4, 400, 65),
        Flight(13, 1, 220, 5, 320, 40),
        Flight(14, 2, 300, 5, 400, 50),
        Flight(15, 5, 420, 4, 520, 45),
        Flight(16, 0, 300, 1, 400, 45),
        Flight(17, 1, 420, 3, 520, 55),
        Flight(18, 3, 540, 4, 640, 50),
        Flight(19, 0, 50, 1, 150, 60),
        Flight(20, 1, 170, 2, 270, 40),
        Flight(21, 2, 290, 4, 390, 45),
        Flight(22, 0, 150, 6, 250, 45),
        Flight(23, 6, 270, 5, 370, 40),
        Flight(24, 6, 270, 3, 370, 50),
        Flight(25, 6, 270, 4, 400, 60),
        Flight(26, 0, 200, 7, 300, 35),
        Flight(27, 7, 320, 5, 420, 40),
        Flight(28, 7, 320, 6, 420, 45),
        Flight(29, 7, 320, 4, 450, 70),
    ]

    # Define all test cases
    all_test_cases = [
        # Basic test cases
        TestCase("Regular Route", "Standard route with multiple options", 0, 4, 0, 700),
        TestCase("Tight Window", "Route with tight time constraints", 0, 4, 100, 500),
        TestCase("Intermediate Destination", "Route to intermediate city", 0, 3, 0, 700),
        TestCase("Early Time Window", "Route in early time period", 0, 2, 0, 300),

        # Edge cases
        TestCase("No Flights Available", "No flights available from start to end city.", 0, 5, 0, 1000),
        TestCase("Single Flight Only", "Only one flight available directly from start to end city.", 0, 1, 0, 100),
        TestCase("Multiple Routes Same Cost", "Multiple routes with same total fare but different flight counts.", 0, 4,
                 0, 700),
        TestCase("Late Arrival", "Route that arrives after allowed time window.", 0, 4, 0, 200),
        TestCase("Early Departure", "Route that departs before allowed time window.", 0, 4, 50, 700),
        TestCase("Direct vs Multi-hop", "Direct flight available but expensive vs cheaper multi-hop", 0, 2, 0, 300),

        # Connection time test cases
        TestCase("Minimum Connection Time", "Testing exactly 20 minutes connection time", 0, 4, 0, 700),
        TestCase("Tight Connections", "Multiple tight connections (close to 20 minutes)", 0, 4, 100, 600),
        TestCase("Long Layovers", "Routes with long connection times", 0, 4, 0, 1000),
        TestCase("Invalid Connection Time", "Routes with less than 20 minutes connection", 0, 4, 0, 500),

        # Complex routing test cases
        TestCase("Multiple Valid Paths", "Multiple equally valid paths to destination", 0, 4, 0, 1000),
        TestCase("Complex Multi-City", "Route through multiple intermediate cities", 0, 4, 100, 800),
        TestCase("Circular Routes", "Possible circular routing through cities", 0, 4, 0, 1000),
        TestCase("Maximum Connections", "Route requiring maximum possible connections", 0, 4, 0, 1000),

        # Time window test cases
        TestCase("Exact Time Window", "Route fitting exactly in time window", 0, 4, 100, 500),
        TestCase("Very Tight Window", "Extremely narrow time window", 0, 4, 200, 300),
        TestCase("Wide Time Window", "Very wide time window with many options", 0, 4, 0, 1000),
        TestCase("Off-Peak Times", "Routes during off-peak hours", 0, 4, 50, 150),

        # Cost optimization test cases
        TestCase("Price vs Time", "Trade-off between price and journey time", 0, 4, 0, 1000),
        TestCase("Cheap Long Route", "Cheaper route with more connections", 0, 4, 0, 1000),
        TestCase("Premium Direct", "Expensive direct flight vs cheaper options", 0, 4, 0, 700),
        TestCase("Cost vs Connections", "Balance between cost and number of connections", 0, 4, 0, 800),

        # Special cases
        TestCase("Same City", "Start and end city are the same", 0, 0, 0, 1000),
        TestCase("All Cities", "Route passing through maximum cities", 0, 4, 0, 1000),
        TestCase("Remote City", "Route to less connected city", 0, 7, 0, 1000),
        TestCase("Hub Transfer", "Route through major hub cities", 0, 4, 0, 1000),

        # Stress test cases
        TestCase("Maximum Time Range", "Route with maximum possible time range", 0, 4, 0, 9999),
        TestCase("Minimum Time Range", "Route with minimum viable time range", 0, 4, 100, 101),
        TestCase("All Options", "Time range including all possible flights", 0, 4, 0, 1000),
        TestCase("Peak Time", "Route during peak time with many options", 0, 4, 200, 500),

        # Optimization priority test cases
        TestCase("Time Priority", "Route prioritizing arrival time", 0, 4, 0, 700),
        TestCase("Cost Priority", "Route prioritizing minimum cost", 0, 4, 0, 1000),
        TestCase("Balance Priority", "Route balancing time, cost and connections", 0, 4, 0, 800),
        TestCase("Connection Priority", "Route minimizing number of connections", 0, 4, 0, 1000),

        # Invalid cases
        TestCase("Invalid Time Window", "End time before start time", 0, 4, 500, 100),
        TestCase("Impossible Route", "No possible route within constraints", 0, 4, 0, 10),
        TestCase("Disconnected Cities", "No route exists between cities", 0, 9, 0, 1000),
        TestCase("Invalid Connection", "No valid connections possible", 0, 4, 100, 150),

        # Add these challenging test cases to the existing all_test_cases list:

        # Complex Optimization Conflict Cases
        TestCase(
            "Optimization_Tradeoff_1",
            "Direct expensive flight vs multiple cheap flights arriving earlier",
            0, 4, 100, 800,
        ),
        TestCase(
            "Optimization_Tradeoff_2",
            "Multiple routes with same number of flights but varying costs and arrival times",
            0, 4, 0, 1000,
        ),

        # Time Window Edge Cases
        TestCase(
            "Critical_Connection",
            "Only one possible connection timing that exactly meets 20-minute requirement",
            0, 4, 100, 400,
        ),
        TestCase(
            "Multiple_Valid_Same_Cost",
            "Multiple routes with identical total cost but different flight counts",
            0, 4, 0, 1000,
        ),

        # Complex Route Structure Cases
        TestCase(
            "Hub_Spoke_Complex",
            "Multiple hub options with different cost/time tradeoffs",
            0, 4, 100, 900,
        ),
        TestCase(
            "Parallel_Routes",
            "Multiple parallel routes with same flight count but different costs",
            0, 4, 0, 800,
        ),

        # Deceptive Cases
        TestCase(
            "False_Optimal",
            "Seemingly optimal direct route but better indirect options exist",
            0, 4, 100, 700,
        ),
        TestCase(
            "Hidden_Optimal",
            "Optimal route requires counter-intuitive intermediate stops",
            0, 4, 0, 1000,
        ),

        # Corner Cases
        TestCase(
            "Last_Minute_Connection",
            "Only one valid route using last possible flights within time window",
            0, 4, 100, 500,
        ),
        TestCase(
            "Early_Bird_Special",
            "Cheaper flights available only in early time window",
            0, 4, 0, 300,
        ),

        # Special Network Structure Cases
        TestCase(
            "Diamond_Network",
            "Multiple parallel paths with different characteristics",
            0, 4, 0, 1000,
        ),
        TestCase(
            "Circular_Network",
            "Possible circular routing that might be optimal",
            0, 4, 100, 800,
        ),

        # Time-Cost Tradeoff Cases
        TestCase(
            "Time_Cost_Conflict",
            "Earlier arrival requires significantly higher cost",
            0, 4, 0, 1000,
        ),
        TestCase(
            "Cost_Time_Balance",
            "Multiple routes with different time-cost balance points",
            0, 4, 100, 900,
        ),

        # Complex Network Flow Cases
        TestCase(
            "Bottleneck_Route",
            "Limited options through mandatory intermediate city",
            0, 4, 100, 800,
        ),
        TestCase(
            "Multi_Hub_Challenge",
            "Multiple hub cities with complex interconnections",
            0, 4, 0, 1000,
        ),

        # Stress Test Cases
        TestCase(
            "Maximum_Complexity",
            "Maximum possible intermediate cities with multiple options each",
            0, 4, 0, 1000,
        ),
        TestCase(
            "Time_Window_Stress",
            "Very narrow time windows forcing specific route choices",
            0, 4, 300, 400,
        ),

        # Dynamic Pricing Cases
        TestCase(
            "Price_Time_Correlation",
            "Earlier flights consistently more expensive",
            0, 4, 0, 1000,
        ),
        TestCase(
            "Inverse_Price_Time",
            "Later flights consistently more expensive",
            0, 4, 100, 900,
        ),

        # Network Structure Edge Cases
        TestCase(
            "Mandatory_Expensive_Hub",
            "Must pass through expensive hub city",
            0, 4, 100, 800,
        ),
        TestCase(
            "Deceptive_Hub_Bypass",
            "Seemingly necessary hub can be bypassed for optimal route",
            0, 4, 0, 1000,
        ),

    ]


    # Add dynamic test cases based on flight data
    def generate_dynamic_test_cases(flights: List[Flight]) -> List[TestCase]:
        """Generate additional test cases based on actual flight data"""
        dynamic_cases = []

        # Find all unique cities
        cities = set()
        for flight in flights:
            cities.add(flight.start_city)
            cities.add(flight.end_city)

        # Find time range
        min_time = min(flight.departure_time for flight in flights)
        max_time = max(flight.arrival_time for flight in flights)

        # Generate cases for each city pair
        for start in cities:
            for end in cities:
                if start != end:
                    dynamic_cases.extend([
                        TestCase(
                            f"Dynamic_{start}_{end}_Full",
                            f"Full time range route from {start} to {end}",
                            start, end, min_time, max_time
                        ), TestCase(
                            f"Dynamic_{start}_{end}_Full",
                            f"Full time range route from {start} to {end}",
                            start, end, min_time, max_time
                        )
                    ])

        return dynamic_cases


    # Combine all test cases
    all_test_cases.extend(generate_dynamic_test_cases(flights))


    # Generated using flight data patterns
    def generate_complex_test_cases(flights):
        complex_cases = []

        # Find all unique cities and time ranges
        cities = set()
        min_time = float('inf')
        max_time = 0
        for flight in flights:
            cities.add(flight.start_city)
            cities.add(flight.end_city)
            min_time = min(min_time, flight.departure_time)
            max_time = max(max_time, flight.arrival_time)

        # Generate complex cases based on actual flight patterns
        for start in cities:
            for end in cities:
                if start != end:
                    # Find natural clusters in departure times
                    departure_times = sorted([f.departure_time for f in flights
                                              if f.start_city == start])
                    if departure_times:
                        mid_time = departure_times[len(departure_times) // 2]
                        complex_cases.extend([
                            TestCase(
                                f"Complex_Pattern_{start}_{end}_Split",
                                "Route choice splits between time periods",
                                start, end,
                                mid_time - 100, mid_time + 100
                            ),
                            TestCase(
                                f"Complex_Pattern_{start}_{end}_Peak",
                                "Maximum flight density period",
                                start, end,
                                mid_time - 50, mid_time + 150
                            )
                        ])

        return complex_cases


    # Add dynamically generated complex cases
    all_test_cases.extend(generate_complex_test_cases(flights))


    # Run tests with comprehensive reporting
    def run_all_tests():
        """Run all tests with detailed reporting"""
        print("\n=== Starting Comprehensive Flight Planner Testing ===\n")

        # Group test cases by category
        categories = {
            "Basic": lambda tc: tc.name.startswith("Regular"),
            "Edge Cases": lambda tc: tc.name.startswith(("No ", "Single", "Multiple")),
            "Connection Time": lambda tc: "Connection" in tc.name,
            "Complex Routing": lambda tc: "Complex" in tc.name or "Multiple Valid" in tc.name,
            "Time Windows": lambda tc: "Time Window" in tc.name or "Tight Window" in tc.name,
            "Cost Optimization": lambda tc: "Cost" in tc.name or "Price" in tc.name,
            "Special Cases": lambda tc: tc.name.startswith(("Same", "All", "Remote")),
            "Stress Tests": lambda tc: tc.name.startswith("Maximum") or tc.name.startswith("Minimum"),
            "Dynamic": lambda tc: tc.name.startswith("Dynamic"),
            "Invalid": lambda tc: tc.name.startswith("Invalid") or "Impossible" in tc.name
        }

        # Run tests by category
        results = {}
        for category, filter_func in categories.items():
            category_cases = list(filter(filter_func, all_test_cases))
            print(f"\n--- Running {category} Tests ---")
            category_results = run_test_cases(category_cases)
            results[category] = category_results
            print(f"--- {category} Tests Complete ---")

        # Print summary report
        print("\n=== Test Summary ===")
        total_passed = sum(res['passed'] for res in results.values())
        total_failed = sum(res['failed'] for res in results.values())
        total_tests = total_passed + total_failed

        print(f"Total Tests Run: {total_tests}")
        print(f"Total Passed: {total_passed}")
        print(f"Total Failed: {total_failed}")
        print(f"Overall Success Rate: {(total_passed / total_tests) * 100:.2f}%")

        print("\nResults by Category:")
        for category, res in results.items():
            print(f"  {category}:")
            print(f"    Passed: {res['passed']}, Failed: {res['failed']}")
            print(f"    Success Rate: {(res['passed'] / (res['passed'] + res['failed'])) * 100:.2f}%")

        print("\n=== Comprehensive Testing Complete ===")


    def validate_route(route, test_case, route_name, all_valid_routes):
        """Validate a single route"""
        if not route:
            print(f"{route_name}: No route found")
            return len(all_valid_routes) == 0  # Valid only if no routes exist

        # Check if route starts and ends at correct cities
        if route[0].start_city != test_case.start_city or route[-1].end_city != test_case.end_city:
            print(f"❌ {route_name}: Invalid start or end city")
            return False

        # Check time constraints
        if route[0].departure_time < test_case.time_start or route[-1].arrival_time > test_case.time_end:
            print(f"❌ {route_name}: Route violates time constraints")
            return False

        # Check connection times
        for i in range(len(route) - 1):
            if route[i + 1].departure_time - route[i].arrival_time < 20:
                print(f"❌ {route_name}: Invalid connection time between flights")
                return False

        # Specific checks for each route type
        if route_name == "Route 1 (Least Flights, Earliest)":
            min_flights = min(len(r) for r in all_valid_routes)
            if len(route) > min_flights:
                print(f"❌ {route_name}: Not the route with fewest flights")
                return False
            earliest_arrival = min(r[-1].arrival_time for r in all_valid_routes if len(r) == min_flights)
            if route[-1].arrival_time > earliest_arrival:
                print(f"❌ {route_name}: Not the earliest arrival among routes with fewest flights")
                return False
        elif route_name == "Route 2 (Cheapest)":
            # Calculate the minimum fare among all valid routes
            min_fare = min(sum(f.fare for f in r) for r in all_valid_routes)

            # Calculate the fare of the current route
            current_route_fare = sum(f.fare for f in route)

            # Check if the current route fare is greater than the minimum fare
            if current_route_fare > min_fare:
                print(f"Current route fare: {current_route_fare}, Minimum fare: {min_fare}")

                # Print all valid routes and their fares
                print("All valid routes and their fares:")
                for valid_route in all_valid_routes:
                    valid_route_fare = sum(f.fare for f in valid_route)
                    print(
                        f"Route: {[f'{f.start_city}->{f.end_city} (Fare: {f.fare})' for f in valid_route]}, Total Fare: {valid_route_fare}")

                print(f"❌ {route_name}: Not the cheapest route")
                return False

        elif route_name == "Route 3 (Least Flights, Cheapest)":
            min_flights = min(len(r) for r in all_valid_routes)
            if len(route) > min_flights:
                print(f"❌ {route_name}: Not the route with fewest flights")
                return False
            min_fare_for_min_flights = min(sum(f.fare for f in r) for r in all_valid_routes if len(r) == min_flights)
            if sum(f.fare for f in route) > min_fare_for_min_flights:
                print(f"❌ {route_name}: Not the cheapest among routes with fewest flights")
                return False

        print(f"✅ {route_name}: Valid")
        return True


    def run_test_cases(test_cases):
        """Run a set of test cases and return results"""
        passed = 0
        failed = 0
        for test_case in test_cases:
            print(f"\nRunning Test: {test_case.name}")
            print(f"Description: {test_case.description}")
            # try:
            planner = Planner(flights)

            # Find all valid routes
            all_valid_routes = find_all_valid_routes(flights, test_case.start_city, test_case.end_city,
                                                     test_case.time_start, test_case.time_end)

            route1 = planner.least_flights_ealiest_route(
                test_case.start_city, test_case.end_city,
                test_case.time_start, test_case.time_end
            )
            route2 = planner.cheapest_route(
                test_case.start_city, test_case.end_city,
                test_case.time_start, test_case.time_end
            )
            route3 = planner.least_flights_cheapest_route(
                test_case.start_city, test_case.end_city,
                test_case.time_start, test_case.time_end
            )

            # Validate routes
            if validate_route(route1, test_case, "Route 1 (Least Flights, Earliest)", all_valid_routes) and \
                    validate_route(route2, test_case, "Route 2 (Cheapest)", all_valid_routes) and \
                    validate_route(route3, test_case, "Route 3 (Least Flights, Cheapest)", all_valid_routes):
                print("✅ Test Passed")
                passed += 1
            else:
                print("❌ Test Failed")
                exit(1)
                # failed += 1
            # except Exception as e:
            #     print(f"❌ Test Failed due to error: {str(e)}")
            #     failed += 1

        return {'passed': passed, 'failed': failed}


    def find_all_valid_routes(flights, start_city, end_city, t1, t2):
        """Find all valid routes between start_city and end_city within time constraints"""
        # This is a simplified version. You might need a more efficient algorithm for large datasets.
        valid_routes = []
        if start_city == end_city:
            return []

        def dfs(current_city, current_time, current_route):
            if current_city == end_city and current_time <= t2:
                valid_routes.append(current_route[:])
                return

            for flight in flights:
                if flight.start_city == current_city and flight.departure_time >= current_time and flight.arrival_time <= t2:
                    if not current_route or flight.departure_time - current_route[-1].arrival_time >= 20:
                        current_route.append(flight)
                        dfs(flight.end_city, flight.arrival_time, current_route)
                        current_route.pop()

        dfs(start_city, t1, [])
        return valid_routes


    # Run all tests
    run_all_tests()

if __name__ == "__main__":
    # Run the comprehensive tests
    run_all_tests()

    # Optionally, you can add more specific tests or performance measurements here
    # For example:
    # measure_performance()
    # test_edge_cases()
    # test_large_scale_scenarios()