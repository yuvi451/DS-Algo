from straw_hat import StrawHatTreasury
from treasure import Treasure
import time


def run_test_case(n=1e3):
    m = 4
    size = 3 * n + 30
    treasury = StrawHatTreasury(m)
    t = 1

    for i in range(1, 31):
        treasury.add_treasure(Treasure(id=i, size=size, arrival_time=i + t))
        size -= 1
        if (i % 3 == 0):
            t = t + 1
    size -= 10
    treasure1 = treasury.get_completion_time()
    for treasure in treasure1:
        print(f"Completion Time: {treasure.completion_time} time+size: {treasure.size + treasure.arrival_time}")

    for i in range(31, 34):
        treasury.add_treasure(Treasure(i, size=size, arrival_time=i+t))
        size-=1
    print("treasure2")
    treasure2=treasury.get_completion_time()
    for treasure in treasure2:
        print(f"Completion Time: {treasure.completion_time} time+size: {treasure.size+treasure.arrival_time}")

    for i in range(34, 37):
        treasury.add_treasure(Treasure(i, size=size, arrival_time=i+27147-50))
        size-=1

    treasure3=treasury.get_completion_time()

    print("treasure3 ")
    for treasure in treasure3:
        print(f"Completion Time: {treasure.completion_time} time+size: {treasure.size+treasure.arrival_time}")
        if(treasure.size+treasure.arrival_time > treasure.completion_time):
            print("ERROR")
            exit(1)
    return treasury.get_completion_time()


def main():

    completed_treasures = run_test_case(1e3)
    print("COMPLETED")


if __name__ == "__main__":
    main()
