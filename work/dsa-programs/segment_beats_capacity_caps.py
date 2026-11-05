class CapacityCapTree:
    def __init__(self, capacities):
        if not capacities:
            raise ValueError("at least one capacity is required")
        self.length = len(capacities)
        size = 4 * self.length
        self.maximum = [float("-inf")] * size
        self.second = [float("-inf")] * size
        self.max_count = [0] * size
        self.total = [0] * size
        self._build(1, 0, self.length, capacities)

    def _pull(self, node):
        left, right = node * 2, node * 2 + 1
        self.total[node] = self.total[left] + self.total[right]
        top = max(self.maximum[left], self.maximum[right])
        self.maximum[node] = top
        self.max_count[node] = sum(self.max_count[child] for child in (left, right)
                                   if self.maximum[child] == top)
        self.second[node] = max(self.second[child] if self.maximum[child] == top
                                else self.maximum[child] for child in (left, right))

    def _build(self, node, start, stop, capacities):
        if stop - start == 1:
            self.maximum[node] = self.total[node] = capacities[start]
            self.max_count[node] = 1
            return
        middle = (start + stop) // 2
        self._build(node * 2, start, middle, capacities)
        self._build(node * 2 + 1, middle, stop, capacities)
        self._pull(node)

    def _cap_node(self, node, limit):
        if self.maximum[node] <= limit:
            return
        assert self.second[node] < limit
        self.total[node] -= (self.maximum[node] - limit) * self.max_count[node]
        self.maximum[node] = limit

    def _push(self, node):
        for child in (node * 2, node * 2 + 1):
            if self.maximum[child] > self.maximum[node]:
                self._cap_node(child, self.maximum[node])

    def cap(self, left, right, limit):
        if not 0 <= left <= right <= self.length:
            raise IndexError("invalid half-open range")
        self._cap(1, 0, self.length, left, right, limit)

    def _cap(self, node, start, stop, left, right, limit):
        if right <= start or stop <= left or self.maximum[node] <= limit:
            return
        if left <= start and stop <= right and self.second[node] < limit:
            self._cap_node(node, limit)
            return
        self._push(node)
        middle = (start + stop) // 2
        self._cap(node * 2, start, middle, left, right, limit)
        self._cap(node * 2 + 1, middle, stop, left, right, limit)
        self._pull(node)

    def sum_range(self, left, right):
        if not 0 <= left <= right <= self.length:
            raise IndexError("invalid half-open range")
        return self._sum(1, 0, self.length, left, right)

    def _sum(self, node, start, stop, left, right):
        if right <= start or stop <= left:
            return 0
        if left <= start and stop <= right:
            return self.total[node]
        self._push(node)
        middle = (start + stop) // 2
        return (self._sum(node * 2, start, middle, left, right)
                + self._sum(node * 2 + 1, middle, stop, left, right))


if __name__ == "__main__":
    capacities = CapacityCapTree([47, 19, 83, 61, 29, 103])
    capacities.cap(1, 5, 47)
    print("after first cap:", capacities.sum_range(0, 6))
    capacities.cap(0, 3, 23)
    print("first three:", capacities.sum_range(0, 3))
    print("last three:", capacities.sum_range(3, 6))
