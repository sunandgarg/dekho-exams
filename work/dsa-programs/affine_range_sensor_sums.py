class AffineReadingTree:
    def __init__(self, readings, modulus=1009):
        if not readings or modulus < 2:
            raise ValueError("need readings and a modulus of at least two")
        self.size = len(readings)
        self.modulus = modulus
        capacity = 4 * self.size
        self.sums = [0] * capacity
        self.pending_multiply = [1] * capacity
        self.pending_add = [0] * capacity

        def build(node, left, right):
            if right - left == 1:
                self.sums[node] = readings[left] % modulus
                return
            middle = (left + right) // 2
            build(node * 2, left, middle)
            build(node * 2 + 1, middle, right)
            self.sums[node] = (self.sums[node * 2] + self.sums[node * 2 + 1]) % modulus

        build(1, 0, self.size)

    def _apply(self, node, length, multiply, add):
        modulus = self.modulus
        self.sums[node] = (multiply * self.sums[node] + add * length) % modulus
        self.pending_multiply[node] = multiply * self.pending_multiply[node] % modulus
        self.pending_add[node] = (multiply * self.pending_add[node] + add) % modulus

    def _push(self, node, left, right):
        if right - left == 1:
            return
        multiply, add = self.pending_multiply[node], self.pending_add[node]
        if multiply == 1 and add == 0:
            return
        middle = (left + right) // 2
        self._apply(node * 2, middle - left, multiply, add)
        self._apply(node * 2 + 1, right - middle, multiply, add)
        self.pending_multiply[node], self.pending_add[node] = 1, 0

    def transform(self, start, stop, multiply, add):
        if not 0 <= start <= stop <= self.size:
            raise IndexError("range must be half-open and within readings")
        multiply %= self.modulus
        add %= self.modulus

        def visit(node, left, right):
            if stop <= left or right <= start:
                return
            if start <= left and right <= stop:
                self._apply(node, right - left, multiply, add)
                return
            self._push(node, left, right)
            middle = (left + right) // 2
            visit(node * 2, left, middle)
            visit(node * 2 + 1, middle, right)
            self.sums[node] = (self.sums[node * 2] + self.sums[node * 2 + 1]) % self.modulus

        visit(1, 0, self.size)

    def range_sum(self, start, stop):
        if not 0 <= start <= stop <= self.size:
            raise IndexError("range must be half-open and within readings")

        def visit(node, left, right):
            if stop <= left or right <= start:
                return 0
            if start <= left and right <= stop:
                return self.sums[node]
            self._push(node, left, right)
            middle = (left + right) // 2
            return (visit(node * 2, left, middle) + visit(node * 2 + 1, middle, right)) % self.modulus

        return visit(1, 0, self.size)


if __name__ == "__main__":
    index = AffineReadingTree([47, 19, 61, 29, 83])
    index.transform(1, 4, 3, 7)
    print(index.range_sum(0, 5), index.range_sum(1, 4))
    index.transform(2, 5, 2, 5)
    print(index.range_sum(0, 5), index.range_sum(2, 5))
