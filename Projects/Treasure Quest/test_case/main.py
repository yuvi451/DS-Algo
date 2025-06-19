import heap
import straw_hat
import treasure
import sys

sys.setrecursionlimit(10 ** 6)


class Parser:
    def __init__(self, filename):
        self.filename = filename
        self.data = []
        self.read_data()

    def read_data(self):
        with open(self.filename, 'r') as f:
            # skip blank lines
            self.data = [line.strip() for line in f if line.strip()]

    def parse(self):
        raise NotImplementedError("Subclasses must implement parse()")


class ParserTreasure(Parser):
    def parse(self):
        if not self.data:
            raise ValueError('Invalid Input: empty file')
        try:
            m = int(self.data[0])
        except ValueError:
            raise ValueError('Invalid Input: first line must be integer')

        treasury = straw_hat.StrawHatTreasury(m)
        for line in self.data[1:]:
            parts = line.split()
            cmd = parts[0]

            if cmd == 'Add':
                if len(parts) != 4:
                    raise ValueError('Invalid Input')
                try:
                    tid = int(parts[1])
                    size = int(parts[2])
                    arrival = int(parts[3])
                except ValueError:
                    raise ValueError('Invalid Input')

                try:
                    t_obj = treasure.Treasure(tid, size, arrival)
                    treasury.add_treasure(t_obj)
                    print(f'Treasure {tid} added to treasury')
                except Exception:
                    print(f'Cannot add treasure {tid} to treasury')

            elif cmd == 'Get':
                if len(parts) != 1:
                    raise ValueError('Invalid Input')
                try:
                    processed = treasury.get_completion_time()
                    results = [(t.id, t.completion_time) for t in processed]
                    print('Completion Time:', results)
                except Exception:
                    print('Cannot get completion time')

            else:
                raise ValueError('Invalid Input')


class ParserHeap(Parser):
    def __init__(self, filename, comparison=lambda a, b: a < b):
        super().__init__(filename)
        self.comp = comparison

    def parse(self):
        h = heap.Heap(self.comp, [])
        count = 0

        for line in self.data:
            parts = line.split()
            if not parts:
                continue
            cmd = parts[0]

            if cmd == 'Insert':
                if len(parts) != 2:
                    raise ValueError('Invalid Input')
                try:
                    value = int(parts[1])
                except ValueError:
                    raise ValueError('Invalid Input')
                try:
                    h.insert(value)
                    count += 1
                    print(f'{value} inserted')
                except Exception:
                    print(f'Cannot insert {value}')

            elif cmd == 'Extract':
                if len(parts) != 1:
                    raise ValueError('Invalid Input')
                try:
                    val = h.extract()
                    count -= 1
                    print(f'{val} extracted')
                except Exception:
                    print('Cannot extract')

            elif cmd == 'Top':
                if len(parts) != 1:
                    raise ValueError('Invalid Input')
                try:
                    top_val = h.top()
                    print(f'Top: {top_val}')
                except Exception:
                    print('Cannot get top')

            elif cmd == 'Print':
                if len(parts) != 1:
                    raise ValueError('Invalid Input')
                try:
                    items = []
                    while count > 0:
                        items.append(str(h.extract()))
                        count -= 1
                    print(' '.join(items))
                except Exception:
                    print('Cannot print')

            else:
                raise ValueError('Invalid Input')


if __name__ == '__main__':
    print("----------tc_heap1.txt----------")
    parser = ParserHeap('tc_heap1.txt')
    parser.parse()
    print()

    print("----------tc_treasury1.txt----------")
    parser = ParserTreasure('tc_treasury1.txt')
    parser.parse()
    print()

    print("----------tc_treasury2.txt----------")
    parser = ParserTreasure('tc_treasury2.txt')
    parser.parse()
    print()
