class DispatchPriorityEnds:
    def __init__(self):
        self.values = []

    @staticmethod
    def _minimum_level(position):
        return ((position + 1).bit_length() - 1) % 2 == 0

    def _bubble(self, position, minimum):
        while position >= 3:
            grandparent = (position - 3) // 4
            better = self.values[position] < self.values[grandparent] if minimum else self.values[position] > self.values[grandparent]
            if not better:
                break
            self.values[position], self.values[grandparent] = self.values[grandparent], self.values[position]
            position = grandparent

    def add(self, priority):
        self.values.append(priority)
        position = len(self.values) - 1
        if position == 0:
            return
        parent = (position - 1) // 2
        minimum = self._minimum_level(position)
        crosses = self.values[position] > self.values[parent] if minimum else self.values[position] < self.values[parent]
        if crosses:
            self.values[position], self.values[parent] = self.values[parent], self.values[position]
            self._bubble(parent, not minimum)
        else:
            self._bubble(position, minimum)

    def _trickle(self, position, minimum):
        while 2 * position + 1 < len(self.values):
            candidates = [child for child in (2 * position + 1, 2 * position + 2,
                                               4 * position + 3, 4 * position + 4,
                                               4 * position + 5, 4 * position + 6)
                          if child < len(self.values)]
            chosen = min(candidates, key=self.values.__getitem__) if minimum else max(candidates, key=self.values.__getitem__)
            better = self.values[chosen] < self.values[position] if minimum else self.values[chosen] > self.values[position]
            if not better:
                break
            self.values[position], self.values[chosen] = self.values[chosen], self.values[position]
            if chosen >= 4 * position + 3:
                parent = (chosen - 1) // 2
                crosses = self.values[chosen] > self.values[parent] if minimum else self.values[chosen] < self.values[parent]
                if crosses:
                    self.values[chosen], self.values[parent] = self.values[parent], self.values[chosen]
                position = chosen
            else:
                break

    def minimum(self):
        return None if not self.values else self.values[0]

    def maximum(self):
        if not self.values:
            return None
        if len(self.values) == 1:
            return self.values[0]
        return max(self.values[1:3])

    def pop_minimum(self):
        if not self.values:
            return None
        result = self.values[0]
        last = self.values.pop()
        if self.values:
            self.values[0] = last
            self._trickle(0, True)
        return result

    def pop_maximum(self):
        if not self.values:
            return None
        if len(self.values) == 1:
            return self.values.pop()
        position = 1 if len(self.values) == 2 or self.values[1] >= self.values[2] else 2
        result = self.values[position]
        last = self.values.pop()
        if position < len(self.values):
            self.values[position] = last
            if self.values[position] < self.values[0]:
                self.values[position], self.values[0] = self.values[0], self.values[position]
            self._trickle(position, False)
        return result


if __name__ == "__main__":
    queue = DispatchPriorityEnds()
    for priority in [47, 19, 61, 29, 83, 37, 47]:
        queue.add(priority)
    print(queue.minimum(), queue.maximum())
    print(queue.pop_minimum(), queue.pop_maximum())
    print(queue.minimum(), queue.maximum(), len(queue.values))
