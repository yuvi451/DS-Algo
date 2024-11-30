import random
import time
from tqdm import tqdm  # For progress bar
from flight import Flight
from planner import Planner


def parse_test_case(file_path):
    with open(file_path, 'r') as file:
        n, m = map(int, file.readline().strip().split())  # Read number of vertices and edges
        flights = []
        cities = set()  # To keep track of all unique cities

        for _ in range(m):
            u, v, cost, start_time, end_time = map(int, file.readline().strip().split())
            flight = Flight(len(flights), u, start_time, v, end_time, cost)
            flights.append(flight)
            cities.update([u, v])  # Add both the start and end cities to the set

    return flights, list(cities)  # Return both flights and list of unique cities


def write_to_output(output_file, message):
    output_file.write(message + "\n")


def main():
    file_path = 'C.txt'
    output_path = 'received_output.txt'

    flights, cities = parse_test_case(file_path)
    flight_planner = Planner(flights)

    # Set random seed for consistent results
    random.seed(13)  # perfect

    # Generate all unique pairs of cities (start_city, destination)
    city_pairs = [(start, dest) for start in cities for dest in cities if start != dest]

    # Randomly select 20 unique pairs
    sampled_pairs = random.sample(city_pairs, 20)

    with open(output_path, 'w') as output_file:
        # Track overall start time
        overall_start_time = time.time()

        # Initialize tqdm progress bar
        for start_city, destination in tqdm(sampled_pairs, desc="Processing city pairs", unit="pair"):
            # Track the start time for this pair
            start_time = time.time()
            write_to_output(output_file, f"\nTesting routes for start_city={start_city}, destination={destination}")

            # Task 1: Least Flights Earliest Route
            route1 = flight_planner.least_flights_ealiest_route(start_city, destination, 0, 3000000000000)
            if route1:
                num_flights_task1 = len(route1)
                arrival_time_task1 = route1[-1].arrival_time if num_flights_task1 > 0 else None
                write_to_output(output_file,
                                f"Task 1: Least Flights Earliest Route - Number of flights: {num_flights_task1}, Arrival time: {arrival_time_task1}")
            else:
                write_to_output(output_file, "Task 1: No route found.")

            # Task 2: Cheapest Route
            route2 = flight_planner.cheapest_route(start_city, destination, 0, 3000000000000)
            if route2:
                total_cost_task2 = sum(flight.fare for flight in route2)
                write_to_output(output_file, f"Task 2: Cheapest Route - Total cost: {total_cost_task2}")
            else:
                write_to_output(output_file, "Task 2: No route found.")

            # Task 3: Least Flights Cheapest Route
            route3 = flight_planner.least_flights_cheapest_route(start_city, destination, 0, 30000000000)
            if route3:
                num_flights_task3 = len(route3)
                total_cost_task3 = sum(flight.fare for flight in route3)
                write_to_output(output_file,
                                f"Task 3: Least Flights Cheapest Route - Number of flights: {num_flights_task3}, Total cost: {total_cost_task3}")
            else:
                write_to_output(output_file, "Task 3: No route found.")

            # Calculate and log time taken for this pair
            time_taken = time.time() - start_time
            write_to_output(output_file,
                            f"Time taken for start_city={start_city}, destination={destination}: {time_taken:.2f} seconds\n")

        # Calculate and log overall time taken
        overall_time_taken = time.time() - overall_start_time
        write_to_output(output_file, f"Total time taken for all tests: {overall_time_taken:.2f} seconds")


if __name__ == "__main__":
    main()