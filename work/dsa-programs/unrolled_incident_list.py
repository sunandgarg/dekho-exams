class IncidentBlock:
    def __init__(self, items, next_block=None):
        self.items = items
        self.next = next_block


class UnrolledIncidentList:
    def __init__(self, block_capacity=4):
        if block_capacity < 2:
            raise ValueError("block capacity must be at least two")
        self.capacity = block_capacity
        self.head = None
        self.tail = None
        self.length = 0

    def __len__(self):
        return self.length

    def _locate(self, index):
        previous = None
        block = self.head
        remaining = index
        while block is not None:
            if remaining < len(block.items):
                return previous, block, remaining
            remaining -= len(block.items)
            previous, block = block, block.next
        raise IndexError("index outside incident list")

    def append(self, incident_id):
        if self.tail is None or len(self.tail.items) == self.capacity:
            block = IncidentBlock([])
            if self.tail is None:
                self.head = block
            else:
                self.tail.next = block
            self.tail = block
        self.tail.items.append(incident_id)
        self.length += 1

    def insert(self, index, incident_id):
        if not 0 <= index <= self.length:
            raise IndexError("insert outside incident list")
        if index == self.length:
            self.append(incident_id)
            return
        _, block, offset = self._locate(index)
        block.items.insert(offset, incident_id)
        self.length += 1
        if len(block.items) > self.capacity:
            middle = len(block.items) // 2
            following = IncidentBlock(block.items[middle:], block.next)
            block.items = block.items[:middle]
            block.next = following
            if self.tail is block:
                self.tail = following

    def delete(self, index):
        if not 0 <= index < self.length:
            raise IndexError("delete outside incident list")
        previous, block, offset = self._locate(index)
        removed = block.items.pop(offset)
        self.length -= 1
        if not block.items:
            if previous is None:
                self.head = block.next
            else:
                previous.next = block.next
            if self.tail is block:
                self.tail = previous
        elif block.next and len(block.items) + len(block.next.items) <= self.capacity:
            following = block.next
            block.items.extend(following.items)
            block.next = following.next
            if self.tail is following:
                self.tail = block
        return removed

    def at(self, index):
        if not 0 <= index < self.length:
            raise IndexError("index outside incident list")
        _, block, offset = self._locate(index)
        return block.items[offset]

    def values(self):
        result = []
        block = self.head
        while block is not None:
            result.extend(block.items)
            block = block.next
        return result


log = UnrolledIncidentList(block_capacity=3)
for incident in ("alert-47", "alert-19", "alert-61", "alert-83"):
    log.append(incident)
log.insert(2, "alert-29")
log.delete(1)
print("order=", log.values(), " third=", log.at(2), sep="")
