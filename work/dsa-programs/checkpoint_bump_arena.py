class CheckpointArena:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.storage = bytearray(capacity)
        self.cursor = 0
        self.next_handle = 0
        self.next_mark = 0
        self.active = {}
        self.marks = []

    def allocate(self, size, alignment=1):
        if size < 1 or alignment < 1 or alignment & (alignment - 1):
            raise ValueError("size must be positive and alignment a power of two")
        start = (self.cursor + alignment - 1) & -alignment
        if start + size > len(self.storage):
            raise MemoryError("arena exhausted")
        handle = self.next_handle
        self.next_handle += 1
        self.storage[start:start + size] = bytes(size)
        self.active[handle] = (start, size)
        self.cursor = start + size
        return handle

    def span(self, handle):
        return self.active[handle]

    def write(self, handle, payload):
        start, size = self.active[handle]
        if len(payload) > size:
            raise ValueError("payload exceeds allocation")
        self.storage[start:start + len(payload)] = payload

    def read(self, handle):
        start, size = self.active[handle]
        return bytes(self.storage[start:start + size])

    def mark(self):
        token = (self.next_mark, self.cursor, self.next_handle)
        self.next_mark += 1
        self.marks.append(token)
        return token

    def rewind(self, token):
        if token not in self.marks:
            raise ValueError("unknown checkpoint")
        _, self.cursor, first_invalid = token
        self.active = {handle: span for handle, span in self.active.items()
                       if handle < first_invalid}
        self.marks = self.marks[:self.marks.index(token)]

    def reset(self):
        self.cursor = 0
        self.active.clear()
        self.marks.clear()


arena = CheckpointArena(64)
stable = arena.allocate(7, alignment=8)
arena.write(stable, b"PUMP-47")
checkpoint = arena.mark()
discarded = arena.allocate(12, alignment=8)
old_offset = arena.span(discarded)[0]
arena.rewind(checkpoint)
reused = arena.allocate(12, alignment=8)
print("stable=", arena.read(stable).decode(), " reused=", arena.span(reused)[0] == old_offset,
      " stale=", discarded not in arena.active, sep="")
