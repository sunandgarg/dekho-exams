class ClockPageCache:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.frames = [None] * capacity
        self.referenced = [False] * capacity
        self.positions = {}
        self.hand = 0
        self.used = 0

    def get(self, page_id):
        position = self.positions[page_id]
        self.referenced[position] = True
        return self.frames[position][1]

    def put(self, page_id, payload):
        if page_id in self.positions:
            position = self.positions[page_id]
            self.frames[position] = (page_id, payload)
            self.referenced[position] = True
            return None
        if self.used < len(self.frames):
            position = self.used
            self.used += 1
        else:
            while self.referenced[self.hand]:
                self.referenced[self.hand] = False
                self.hand = (self.hand + 1) % len(self.frames)
            position = self.hand
        victim = self.frames[position]
        if victim is not None:
            del self.positions[victim[0]]
        self.frames[position] = (page_id, payload)
        self.positions[page_id] = position
        self.referenced[position] = False
        self.hand = (position + 1) % len(self.frames)
        return None if victim is None else victim[0]


pages = ClockPageCache(3)
for page_id in (47, 19, 61):
    pages.put(page_id, f"page-{page_id}")
pages.get(47)
evicted = pages.put(83, "page-83")
print("evicted=", evicted, " resident=", sorted(pages.positions), sep="")
