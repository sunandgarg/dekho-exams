import heapq
import itertools


class DualEndedIncidentQueue:
    def __init__(self):
        self.minimum = []
        self.maximum = []
        self.live = {}
        self.sequence = itertools.count()

    def _compact_if_needed(self):
        if len(self.minimum) + len(self.maximum) <= 3 * len(self.live) + 32:
            return
        self.minimum = [(priority, arrival, incident_id)
                        for incident_id, (priority, arrival) in self.live.items()]
        self.maximum = [(-priority, arrival, incident_id)
                        for incident_id, (priority, arrival) in self.live.items()]
        heapq.heapify(self.minimum)
        heapq.heapify(self.maximum)

    def push(self, priority, incident_id):
        if incident_id in self.live:
            raise ValueError("incident already queued")
        arrival = next(self.sequence)
        self.live[incident_id] = (priority, arrival)
        heapq.heappush(self.minimum, (priority, arrival, incident_id))
        heapq.heappush(self.maximum, (-priority, arrival, incident_id))
        self._compact_if_needed()

    def _pop(self, heap, sign):
        while heap:
            stored_priority, arrival, incident_id = heapq.heappop(heap)
            priority = sign * stored_priority
            if self.live.get(incident_id) == (priority, arrival):
                del self.live[incident_id]
                self._compact_if_needed()
                return priority, incident_id
        raise IndexError("empty priority queue")

    def pop_min(self):
        return self._pop(self.minimum, 1)

    def pop_max(self):
        return self._pop(self.maximum, -1)


queue = DualEndedIncidentQueue()
for priority, incident_id in ((47, "pump-47"), (19, "valve-19"),
                              (61, "sensor-61"), (19, "grid-83")):
    queue.push(priority, incident_id)
print("min=", queue.pop_min(), "max=", queue.pop_max(),
      "remaining=", len(queue.live), sep="")
