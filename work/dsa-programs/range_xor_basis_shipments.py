class XorBasis:
    def __init__(self, width=12):
        self.width = width
        self.pivots = [0] * width

    def add(self, value):
        if not 0 <= value < 1 << self.width:
            raise ValueError("value outside the configured bit width")
        for bit in range(self.width - 1, -1, -1):
            if not value & (1 << bit):
                continue
            if self.pivots[bit]:
                value ^= self.pivots[bit]
            else:
                self.pivots[bit] = value
                return

    def absorb(self, other):
        for pivot in other.pivots:
            if pivot:
                self.add(pivot)

    def maximum(self):
        result = 0
        for pivot in reversed(self.pivots):
            result = max(result, result ^ pivot)
        return result

    def can_make(self, target):
        if not 0 <= target < 1 << self.width:
            return False
        for bit in range(self.width - 1, -1, -1):
            if target & (1 << bit):
                if not self.pivots[bit]:
                    return False
                target ^= self.pivots[bit]
        return True

    def rank(self):
        return sum(bool(pivot) for pivot in self.pivots)


class RangeXorBasis:
    def __init__(self, shipment_flags, width=12):
        self.width = width
        self.length = len(shipment_flags)
        self.leaves = 1 << (max(1, self.length) - 1).bit_length()
        self.tree = [XorBasis(width) for _ in range(self.leaves * 2)]
        for position, flags in enumerate(shipment_flags):
            self.tree[self.leaves + position].add(flags)
        for position in range(self.leaves - 1, 0, -1):
            self.tree[position].absorb(self.tree[position * 2])
            self.tree[position].absorb(self.tree[position * 2 + 1])

    def replace(self, position, flags):
        if not 0 <= position < self.length:
            raise IndexError("position outside shipment list")
        position += self.leaves
        self.tree[position] = XorBasis(self.width)
        self.tree[position].add(flags)
        position //= 2
        while position:
            self.tree[position] = XorBasis(self.width)
            self.tree[position].absorb(self.tree[position * 2])
            self.tree[position].absorb(self.tree[position * 2 + 1])
            position //= 2

    def basis(self, start, stop):
        if not 0 <= start <= stop <= self.length:
            raise IndexError("query must be a valid half-open range")
        answer = XorBasis(self.width)
        start += self.leaves
        stop += self.leaves
        while start < stop:
            if start & 1:
                answer.absorb(self.tree[start])
                start += 1
            if stop & 1:
                stop -= 1
                answer.absorb(self.tree[stop])
            start //= 2
            stop //= 2
        return answer


if __name__ == "__main__":
    index = RangeXorBasis([47, 29, 61, 83, 19])
    selected = index.basis(1, 4)
    print(selected.maximum(), selected.rank(), selected.can_make(29 ^ 61))
    index.replace(2, 37)
    print(index.basis(1, 4).maximum(), index.basis(4, 4).maximum())
