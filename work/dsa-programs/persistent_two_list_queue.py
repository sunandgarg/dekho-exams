class VersionedDispatchQueue:
    def __init__(self, front=None, rear=None, count=0):
        self.front = front
        self.rear = rear
        self.count = count

    @staticmethod
    def _reverse(chain):
        result = None
        while chain is not None:
            result = (chain[0], result)
            chain = chain[1]
        return result

    def _normalized(self):
        if self.front is not None or self.rear is None:
            return self
        return VersionedDispatchQueue(self._reverse(self.rear), None, self.count)

    def enqueue(self, case_id):
        next_version = VersionedDispatchQueue(self.front, (case_id, self.rear), self.count + 1)
        return next_version._normalized()

    def dequeue(self):
        ready = self._normalized()
        if ready.front is None:
            raise IndexError("dispatch queue is empty")
        case_id = ready.front[0]
        next_version = VersionedDispatchQueue(ready.front[1], ready.rear, ready.count - 1)
        return case_id, next_version._normalized()

    def values(self):
        front_values = []
        chain = self.front
        while chain is not None:
            front_values.append(chain[0])
            chain = chain[1]
        rear_values = []
        chain = self.rear
        while chain is not None:
            rear_values.append(chain[0])
            chain = chain[1]
        return front_values + rear_values[::-1]


if __name__ == "__main__":
    morning = VersionedDispatchQueue().enqueue(47).enqueue(19).enqueue(83)
    served_id, midday = morning.dequeue()
    afternoon = midday.enqueue(61)
    print("served:", served_id)
    print("morning:", morning.values())
    print("afternoon:", afternoon.values())
