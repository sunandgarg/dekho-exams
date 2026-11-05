from bisect import bisect_right


class SegmentedIncidentArray:
    def __init__(self, block_capacity=4):
        if block_capacity < 2:
            raise ValueError("block capacity must be at least two")
        self.capacity = block_capacity
        self.blocks = []
        self.ends = []

    def __len__(self):
        return self.ends[-1] if self.ends else 0

    def _position(self, index):
        block_index = bisect_right(self.ends, index)
        previous_end = self.ends[block_index - 1] if block_index else 0
        return block_index, index - previous_end

    def _refresh_from(self, block_index):
        running = self.ends[block_index - 1] if block_index else 0
        for offset in range(block_index, len(self.blocks)):
            running += len(self.blocks[offset])
            self.ends[offset] = running

    def append(self, incident_id):
        if not self.blocks or len(self.blocks[-1]) == self.capacity:
            self.blocks.append([])
            self.ends.append(len(self))
        self.blocks[-1].append(incident_id)
        self.ends[-1] += 1

    def at(self, index):
        if not 0 <= index < len(self):
            raise IndexError("index outside incident array")
        block_index, offset = self._position(index)
        return self.blocks[block_index][offset]

    def insert(self, index, incident_id):
        if not 0 <= index <= len(self):
            raise IndexError("insert outside incident array")
        if index == len(self):
            self.append(incident_id)
            return
        block_index, offset = self._position(index)
        block = self.blocks[block_index]
        block.insert(offset, incident_id)
        if len(block) > self.capacity:
            middle = len(block) // 2
            self.blocks.insert(block_index + 1, block[middle:])
            self.ends.insert(block_index + 1, 0)
            del block[middle:]
        self._refresh_from(block_index)

    def delete(self, index):
        if not 0 <= index < len(self):
            raise IndexError("delete outside incident array")
        block_index, offset = self._position(index)
        block = self.blocks[block_index]
        removed = block.pop(offset)
        if not block:
            self.blocks.pop(block_index)
            self.ends.pop(block_index)
        elif block_index + 1 < len(self.blocks) and len(block) + len(self.blocks[block_index + 1]) <= self.capacity:
            block.extend(self.blocks.pop(block_index + 1))
            self.ends.pop(block_index + 1)
        self._refresh_from(block_index)
        return removed

    def values(self):
        return [incident for block in self.blocks for incident in block]


events = SegmentedIncidentArray(block_capacity=3)
for incident in ("alert-47", "alert-19", "alert-61", "alert-83"):
    events.append(incident)
events.insert(2, "alert-29")
events.delete(1)
print("order=", events.values(), " third=", events.at(2), sep="")
