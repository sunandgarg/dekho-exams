
class MonotoneIncidentQueue:
    def __init__(self):
        self.last = 0
        self.buckets = [[]]
        self.size = 0

    def push(self, priority, incident_id):
        if not isinstance(priority, int) or priority < self.last:
            raise ValueError("priority must be an integer at least the last extracted priority")
        level = (priority ^ self.last).bit_length()
        while len(self.buckets) <= level:
            self.buckets.append([])
        self.buckets[level].append((priority, incident_id))
        self.size += 1

    def pop(self):
        if not self.size:
            raise IndexError("empty priority queue")
        if not self.buckets[0]:
            level = next(index for index, bucket in enumerate(self.buckets) if bucket)
            pending = self.buckets[level]
            self.buckets[level] = []
            self.last = min(priority for priority, _ in pending)
            for entry in pending:
                new_level = (entry[0] ^ self.last).bit_length()
                self.buckets[new_level].append(entry)
        self.size -= 1
        return self.buckets[0].pop()


queue = MonotoneIncidentQueue()
for priority, incident_id in ((47, "pump-47"), (19, "valve-19"),
                              (61, "sensor-61"), (19, "grid-83")):
    queue.push(priority, incident_id)
print("priorities=", [queue.pop()[0] for _ in range(4)], sep="")
