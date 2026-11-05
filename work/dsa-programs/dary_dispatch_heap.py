class DaryDispatchHeap:
    def __init__(self, arity=4):
        if arity < 2:
            raise ValueError("arity must be at least two")
        self.arity = arity
        self.values = []
        self.serial = 0

    def push(self, priority, incident_id):
        self.serial += 1
        entry = (priority, self.serial, incident_id)
        self.values.append(entry)
        child = len(self.values) - 1
        while child:
            parent = (child - 1) // self.arity
            if self.values[parent] <= entry:
                break
            self.values[child] = self.values[parent]
            child = parent
        self.values[child] = entry

    def pop(self):
        if not self.values:
            raise IndexError("empty dispatch heap")
        winner = self.values[0]
        last = self.values.pop()
        if self.values:
            parent = 0
            size = len(self.values)
            while True:
                first = parent * self.arity + 1
                if first >= size:
                    break
                best = min(range(first, min(first + self.arity, size)), key=self.values.__getitem__)
                if last <= self.values[best]:
                    break
                self.values[parent] = self.values[best]
                parent = best
            self.values[parent] = last
        return winner[2]


if __name__ == "__main__":
    dispatch = DaryDispatchHeap(4)
    for priority, incident_id in [(47, "pump"), (19, "valve"), (19, "sensor"), (61, "grid")]:
        dispatch.push(priority, incident_id)
    print("order=", [dispatch.pop() for _ in range(4)], sep="")
