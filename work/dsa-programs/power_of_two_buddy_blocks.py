class BuddyBlockPool:
    def __init__(self, capacity):
        if capacity < 1 or capacity & (capacity - 1):
            raise ValueError("capacity must be a power of two")
        self.capacity = capacity
        self.max_order = capacity.bit_length() - 1
        self.free_by_order = [set() for _ in range(self.max_order + 1)]
        self.free_by_order[self.max_order].add(0)
        self.allocated = {}

    def allocate(self, requested):
        if requested < 1:
            raise ValueError("requested size must be positive")
        order = (requested - 1).bit_length()
        found = next((level for level in range(order, self.max_order + 1)
                      if self.free_by_order[level]), None)
        if found is None:
            raise MemoryError("no suitable buddy block")
        start = min(self.free_by_order[found])
        self.free_by_order[found].remove(start)
        while found > order:
            found -= 1
            self.free_by_order[found].add(start + (1 << found))
        self.allocated[start] = (order, requested)
        return start

    def release(self, start):
        order, _ = self.allocated.pop(start)
        while order < self.max_order:
            buddy = start ^ (1 << order)
            if buddy not in self.free_by_order[order]:
                break
            self.free_by_order[order].remove(buddy)
            start = min(start, buddy)
            order += 1
        self.free_by_order[order].add(start)

    def free_units(self):
        return sum(len(blocks) * (1 << order)
                   for order, blocks in enumerate(self.free_by_order))


pool = BuddyBlockPool(128)
pump = pool.allocate(13)
valve = pool.allocate(19)
pool.release(pump)
pool.release(valve)
print("free=", pool.free_units(), " root=", sorted(pool.free_by_order[7]), sep="")
