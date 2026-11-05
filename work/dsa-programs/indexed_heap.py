class DispatchHeap:
    def __init__(self):
        self.items = []
        self.position = {}

    def swap(self, left, right):
        self.items[left], self.items[right] = self.items[right], self.items[left]
        self.position[self.items[left][1]] = left
        self.position[self.items[right][1]] = right

    def rise(self, index):
        while index:
            parent = (index - 1) // 2
            if self.items[parent] <= self.items[index]:
                break
            self.swap(parent, index)
            index = parent

    def sink(self, index):
        size = len(self.items)
        while 2 * index + 1 < size:
            child = 2 * index + 1
            if child + 1 < size and self.items[child + 1] < self.items[child]:
                child += 1
            if self.items[index] <= self.items[child]:
                break
            self.swap(index, child)
            index = child

    def add(self, job_id, priority):
        if job_id in self.position:
            raise ValueError("job already queued")
        self.position[job_id] = len(self.items)
        self.items.append((priority, job_id))
        self.rise(len(self.items) - 1)

    def decrease(self, job_id, priority):
        index = self.position[job_id]
        old_priority = self.items[index][0]
        if priority > old_priority:
            raise ValueError("priority increased")
        self.items[index] = (priority, job_id)
        self.rise(index)

    def pop(self):
        if not self.items:
            raise IndexError("dispatch heap is empty")
        result = self.items[0]
        last = self.items.pop()
        del self.position[result[1]]
        if self.items:
            self.items[0] = last
            self.position[last[1]] = 0
            self.sink(0)
        return result


dispatch = DispatchHeap()
for job_id, priority in (("J-47", 9), ("J-52", 6), ("J-61", 12), ("J-83", 7)):
    dispatch.add(job_id, priority)
dispatch.decrease("J-61", 3)
print(dispatch.pop())
print(dispatch.pop())
