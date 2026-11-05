class FirstFitSpanPool:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.free_spans = [(0, capacity)]
        self.allocated = {}

    def allocate(self, size):
        if size < 1:
            raise ValueError("size must be positive")
        for index, (start, length) in enumerate(self.free_spans):
            if length < size:
                continue
            if length == size:
                self.free_spans.pop(index)
            else:
                self.free_spans[index] = (start + size, length - size)
            self.allocated[start] = size
            return start
        raise MemoryError("no contiguous free span fits")

    def release(self, start):
        size = self.allocated.pop(start)
        self.free_spans.append((start, size))
        self.free_spans.sort()
        merged = []
        for span_start, length in self.free_spans:
            if merged and merged[-1][0] + merged[-1][1] == span_start:
                previous_start, previous_length = merged[-1]
                merged[-1] = (previous_start, previous_length + length)
            else:
                merged.append((span_start, length))
        self.free_spans = merged

    def free_units(self):
        return sum(length for _, length in self.free_spans)


pool = FirstFitSpanPool(64)
pump = pool.allocate(13)
valve = pool.allocate(19)
pool.release(pump)
pool.release(valve)
service = pool.allocate(24)
print("service-start=", service, " free=", pool.free_units(),
      " spans=", pool.free_spans, sep="")
