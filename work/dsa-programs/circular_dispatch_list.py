"""Single-tail circular list for a small round-robin dispatch ring."""


class DispatchNode:
    def __init__(self, depot_id):
        self.depot_id = depot_id
        self.next = None


class DispatchRing:
    def __init__(self):
        self.tail = None
        self.length = 0

    def append(self, depot_id):
        node = DispatchNode(depot_id)
        if self.tail is None:
            node.next = node
        else:
            node.next = self.tail.next
            self.tail.next = node
        self.tail = node
        self.length += 1

    def rotate_once(self):
        if self.tail is not None:
            self.tail = self.tail.next

    def remove_front(self):
        if self.tail is None:
            raise IndexError("empty dispatch ring")
        front = self.tail.next
        if front is self.tail:
            self.tail = None
        else:
            self.tail.next = front.next
        self.length -= 1
        front.next = None
        return front.depot_id

    def snapshot(self):
        if self.tail is None:
            return []
        result = []
        current = self.tail.next
        for _ in range(self.length):
            result.append(current.depot_id)
            current = current.next
        return result


dispatch = DispatchRing()
for depot in ("D-19", "D-47", "D-61"):
    dispatch.append(depot)
print(dispatch.snapshot())
dispatch.rotate_once()
print(dispatch.remove_front())
print(dispatch.snapshot())
