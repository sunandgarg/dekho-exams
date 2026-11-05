class PersistentRangeMex:
    def __init__(self, readings):
        self.size = len(readings)
        self.roots = [None]
        for position, reading in enumerate(readings):
            previous = self.roots[-1]
            if isinstance(reading, int) and 0 <= reading <= self.size:
                previous = self._replace(previous, 0, self.size + 1, reading, position)
            self.roots.append(previous)

    @staticmethod
    def _minimum(node):
        return -1 if node is None else node[0]

    def _replace(self, node, left, right, target, position):
        if right - left == 1:
            return position, None, None
        middle = (left + right) // 2
        old_left, old_right = (None, None) if node is None else (node[1], node[2])
        if target < middle:
            old_left = self._replace(old_left, left, middle, target, position)
        else:
            old_right = self._replace(old_right, middle, right, target, position)
        return min(self._minimum(old_left), self._minimum(old_right)), old_left, old_right

    def mex(self, start, stop):
        if not 0 <= start <= stop <= self.size:
            raise IndexError("query must be a valid half-open range")
        node, left, right = self.roots[stop], 0, self.size + 1
        while right - left > 1:
            middle = (left + right) // 2
            left_child = None if node is None else node[1]
            if self._minimum(left_child) < start:
                node, right = left_child, middle
            else:
                node, left = (None if node is None else node[2]), middle
        return left


if __name__ == "__main__":
    index = PersistentRangeMex([0, 3, 1, 0, 2, 7, 1])
    print(index.mex(0, 5), index.mex(2, 7), index.mex(4, 4))
    print(len(index.roots))
