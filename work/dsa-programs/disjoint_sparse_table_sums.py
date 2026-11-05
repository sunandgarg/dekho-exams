class DisjointSumTable:
    def __init__(self, readings):
        self.values = list(readings)
        self.layers = []
        size = len(self.values)
        for level in range(max(0, (size - 1).bit_length())):
            half = 1 << level
            width = half * 2
            layer = [0] * size
            for block_start in range(0, size, width):
                middle = min(block_start + half, size)
                block_stop = min(block_start + width, size)
                if middle > block_start:
                    layer[middle - 1] = self.values[middle - 1]
                    for position in range(middle - 2, block_start - 1, -1):
                        layer[position] = self.values[position] + layer[position + 1]
                if middle < block_stop:
                    layer[middle] = self.values[middle]
                    for position in range(middle + 1, block_stop):
                        layer[position] = layer[position - 1] + self.values[position]
            self.layers.append(layer)

    def sum_between(self, start, stop):
        if not 0 <= start <= stop <= len(self.values):
            raise IndexError("invalid half-open reading range")
        if start == stop:
            return 0
        if stop - start == 1:
            return self.values[start]
        level = (start ^ (stop - 1)).bit_length() - 1
        return self.layers[level][start] + self.layers[level][stop - 1]


if __name__ == "__main__":
    table = DisjointSumTable([23, 47, 19, 61, 38, 52, 29])
    print("window=", table.sum_between(1, 6), sep="")
    print("single=", table.sum_between(3, 4), sep="")
    print("empty=", table.sum_between(2, 2), sep="")
