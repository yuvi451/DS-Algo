import time
from flight import Flight
from planner import Planner


def load_test_cases_from_file(filename):
    test_cases = []
    with open(filename, 'r') as file:
        num_test_cases = int(file.readline().strip())

        for _ in range(num_test_cases):
            n = int(file.readline().strip())
            flights = [
                Flight(*map(int, file.readline().strip().split()))
                for _ in range(n)
            ]
            start_city, end_city, t1, t2 = map(int, file.readline().strip().split())
            test_cases.append((flights, start_city, end_city, t1, t2))

    return test_cases


def format_route(route):
    return "No route found" if not route else [flight.flight_no for flight in route]


def compare_outputs(output_file, model_file):
    with open(output_file, 'r') as out_f, open(model_file, 'r') as model_f:
        output_lines, model_lines = out_f.readlines(), model_f.readlines()

    if len(output_lines) != len(model_lines):
        print(
            f"The number of lines in the output does not match the model output.\nOutput lines: {len(output_lines)}, Model lines: {len(model_lines)}")
        return

    current_test_case = None
    for idx, (out_line, model_line) in enumerate(zip(output_lines, model_lines)):
        out_line, model_line = out_line.strip(), model_line.strip()

        if out_line.startswith("Test Case"):
            current_test_case = out_line
        elif out_line != model_line:
            route_number = "Unknown"
            if out_line.startswith("Route 1:"):
                route_number = 1
                out_line = f"FlightCount - {out_line.split(',')[0].split()[-1]}, ArrivalTime - {out_line.split(',')[-1]}"
                model_line = f"FlightCount - {model_line.split(',')[0].split()[-1]}, ArrivalTime - {model_line.split(',')[-1]}"
            elif out_line.startswith("Route 2:"):
                route_number = 2
                out_line = f"Fare - {out_line.split()[-1]}"
                model_line = f"Fare - {model_line.split()[-1]}"
            elif out_line.startswith("Route 3:"):
                route_number = 3
                out_line = f"FlightCount - {out_line.split(',')[0].split()[-1]}, Fare - {out_line.split(',')[-1]}"
                model_line = f"FlightCount - {model_line.split(',')[0].split()[-1]}, Fare - {model_line.split(',')[-1]}"

            print(
                f"\n😔😞 Your output does not match the correct output.\n* Mismatch in {current_test_case}\n    Your Output: Route {route_number}: {out_line}\n    Expected Output: Route {route_number}: {model_line}\nYour Route {route_number} function is incorrect.\n")
            return

    print("All test cases match the expected output !!! 😊🥳 \n")


def main():
    test_cases = load_test_cases_from_file('fli1000.txt')

    with open('output.txt', 'w') as output_file:
        start_time_total = time.time()

        for i, (flights, start_city, end_city, t1, t2) in enumerate(test_cases, start=1):
            flight_planner = Planner(flights)

            def process_route(route_func, *args):
                start_time = time.time()
                route = route_func(*args)
                return route, time.time() - start_time

            route1, route1_time = process_route(flight_planner.least_flights_ealiest_route, start_city, end_city, t1,
                                                t2)
            route1_flights_count = len(route1) if route1 else 0
            route1_arrival_time = route1[-1].arrival_time if route1 else "No route"

            route2, route2_time = process_route(flight_planner.cheapest_route, start_city, end_city, t1, t2)
            route2_total_cost = sum(flight.fare for flight in route2)

            route3, route3_time = process_route(flight_planner.least_flights_cheapest_route, start_city, end_city, t1,
                                                t2)
            route3_flights_count = len(route3) if route3 else 0
            route3_total_cost = sum(flight.fare for flight in route3)

            print(f"Test Case {i} Processing ...\n")
            output_file.write(f"Test Case {i}:\n")
            output_file.write(f"Route 1: {route1_flights_count}, {route1_arrival_time}\n")
            output_file.write(f"Route 2: {route2_total_cost}\n")
            output_file.write(f"Route 3: {route3_flights_count}, {route3_total_cost}\n\n")

        print(f"Total time taken by your code: {time.time() - start_time_total}")


if __name__ == "__main__":
    main()
    compare_outputs('output.txt', 'model_output.txt')
