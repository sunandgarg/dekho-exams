from math import isqrt


class BlockCapacitySums:
    def __init__(self, capacities):
        self.values = list(capacities)
        self.block_size = max(1, isqrt(len(self.values)))
        self.blocks = [0] * ((len(self.values) + self.block_size - 1) // self.block_size)
        for position, capacity in enumerate(self.values):
            self.blocks[position // self.block_size] += capacity

    def replace(self, position, capacity):
        if not 0 <= position < len(self.values):
            raise IndexError("capacity position outside batch")
        self.blocks[position // self.block_size] += capacity - self.values[position]
        self.values[position] = capacity

    def sum_between(self, start, stop):
        if not 0 <= start <= stop <= len(self.values):
            raise IndexError("invalid half-open capacity range")
        total = 0
        while start < stop:
            if start % self.block_size == 0 and start + self.block_size <= stop:
                total += self.blocks[start // self.block_size]
                start += self.block_size
            else:
                total += self.values[start]
                start += 1
        return total


if __name__ == "__main__":
    ledger = BlockCapacitySums([23, 47, 19, 61, 38, 52, 29])
    print("before=", ledger.sum_between(1, 6), sep="")
    ledger.replace(3, 74)
    print("after=", ledger.sum_between(1, 6), sep="")
    print("empty=", ledger.sum_between(4, 4), sep="")
