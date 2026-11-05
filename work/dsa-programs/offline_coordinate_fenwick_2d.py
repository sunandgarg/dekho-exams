from bisect import bisect_left


class DepotPresenceGrid:
    def __init__(self, possible_points):
        self.points = set(possible_points)
        self.x_values = sorted({x for x, _ in self.points})
        self.y_values = [[] for _ in range(len(self.x_values) + 1)]
        for x, y in self.points:
            slot = bisect_left(self.x_values, x) + 1
            while slot < len(self.y_values):
                self.y_values[slot].append(y)
                slot += slot & -slot
        self.y_values = [sorted(set(values)) for values in self.y_values]
        self.bits = [[0] * (len(values) + 1) for values in self.y_values]
        self.present = set()

    def set_present(self, x, y, enabled):
        point = (x, y)
        if point not in self.points:
            raise KeyError("coordinate absent from frozen catalog")
        if (point in self.present) == enabled:
            return False
        if enabled:
            self.present.add(point)
        else:
            self.present.remove(point)
        delta = 1 if enabled else -1
        slot = bisect_left(self.x_values, x) + 1
        while slot < len(self.y_values):
            position = bisect_left(self.y_values[slot], y) + 1
            while position < len(self.bits[slot]):
                self.bits[slot][position] += delta
                position += position & -position
            slot += slot & -slot
        return True

    def _prefix(self, x_limit, y_limit):
        result = 0
        slot = bisect_left(self.x_values, x_limit)
        while slot:
            position = bisect_left(self.y_values[slot], y_limit)
            while position:
                result += self.bits[slot][position]
                position -= position & -position
            slot -= slot & -slot
        return result

    def rectangle_count(self, x_low, x_high, y_low, y_high):
        if x_low > x_high or y_low > y_high:
            raise ValueError("reversed rectangle")
        return (self._prefix(x_high, y_high) - self._prefix(x_low, y_high)
                - self._prefix(x_high, y_low) + self._prefix(x_low, y_low))


if __name__ == "__main__":
    grid = DepotPresenceGrid([(19, 47), (29, 61), (47, 19), (47, 61), (83, 29)])
    for point in [(19, 47), (29, 61), (47, 19), (47, 61)]:
        grid.set_present(*point, True)
    print("active in [15,60) x [45,65):", grid.rectangle_count(15, 60, 45, 65))
    grid.set_present(47, 61, False)
    print("after removal:", grid.rectangle_count(15, 60, 45, 65))
