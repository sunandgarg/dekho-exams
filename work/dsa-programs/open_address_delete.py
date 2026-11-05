TOMBSTONE = object()


class BayDirectory:
    def __init__(self, capacity=11):
        self.slots = [None] * capacity
        self.live = 0
        self.deleted = 0

    def locate(self, bay_id):
        first_deleted = None
        for offset in range(len(self.slots)):
            index = (bay_id + offset) % len(self.slots)
            entry = self.slots[index]
            if entry is None:
                return first_deleted if first_deleted is not None else index, False
            if entry is TOMBSTONE:
                if first_deleted is None:
                    first_deleted = index
            elif entry[0] == bay_id:
                return index, True
        return first_deleted, False

    def rebuild(self, capacity):
        old_entries = [entry for entry in self.slots if entry is not None and entry is not TOMBSTONE]
        self.slots = [None] * capacity
        self.live = 0
        self.deleted = 0
        for bay_id, owner in old_entries:
            self.put(bay_id, owner)

    def put(self, bay_id, owner):
        if not isinstance(bay_id, int) or bay_id < 0:
            raise ValueError("bay ID must be a nonnegative integer")
        if 10 * (self.live + self.deleted + 1) >= 7 * len(self.slots):
            self.rebuild(2 * len(self.slots) + 1)
        index, found = self.locate(bay_id)
        if found:
            self.slots[index] = bay_id, owner
            return
        if index is None:
            self.rebuild(2 * len(self.slots) + 1)
            index, _ = self.locate(bay_id)
        if self.slots[index] is TOMBSTONE:
            self.deleted -= 1
        self.slots[index] = bay_id, owner
        self.live += 1

    def lookup(self, bay_id):
        index, found = self.locate(bay_id)
        return (True, self.slots[index][1]) if found else (False, None)

    def remove(self, bay_id):
        index, found = self.locate(bay_id)
        if not found:
            return False
        self.slots[index] = TOMBSTONE
        self.live -= 1
        self.deleted += 1
        if self.deleted > self.live and self.deleted > 2:
            self.rebuild(len(self.slots))
        return True


directory = BayDirectory()
for bay_id, owner in ((47, "north"), (58, "east"), (69, "west")):
    directory.put(bay_id, owner)
print(directory.remove(47), directory.lookup(58), directory.lookup(69))
directory.put(80, "south")
print(directory.lookup(80), directory.lookup(47))
