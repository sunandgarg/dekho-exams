class RoadGraphOverlay:
    def __init__(self, vertex_count, road_edges):
        if vertex_count < 0:
            raise ValueError("negative vertex count")
        self.count = vertex_count
        self.offsets, self.targets = self._pack(road_edges)
        self.added = {}
        self.deleted = {}

    def _validate(self, source, target):
        if not (0 <= source < self.count and 0 <= target < self.count):
            raise ValueError("road endpoint outside graph")

    def _pack(self, road_edges):
        rows = [set() for _ in range(self.count)]
        for source, target in road_edges:
            self._validate(source, target)
            rows[source].add(target)
        offsets, targets = [0], []
        for row in rows:
            targets.extend(sorted(row))
            offsets.append(len(targets))
        return offsets, targets

    def neighbors(self, source):
        if not 0 <= source < self.count:
            raise ValueError("source outside graph")
        base = self.targets[self.offsets[source]:self.offsets[source + 1]]
        return sorted((set(base) - self.deleted.get(source, set())) | self.added.get(source, set()))

    def add_road(self, source, target):
        self._validate(source, target)
        self.deleted.setdefault(source, set()).discard(target)
        if target not in self.targets[self.offsets[source]:self.offsets[source + 1]]:
            self.added.setdefault(source, set()).add(target)

    def remove_road(self, source, target):
        self._validate(source, target)
        self.added.setdefault(source, set()).discard(target)
        if target in self.targets[self.offsets[source]:self.offsets[source + 1]]:
            self.deleted.setdefault(source, set()).add(target)

    def compact(self):
        edges = [(source, target) for source in range(self.count) for target in self.neighbors(source)]
        self.offsets, self.targets = self._pack(edges)
        self.added.clear()
        self.deleted.clear()


if __name__ == "__main__":
    roads = RoadGraphOverlay(5, [(0, 1), (0, 3), (1, 2), (3, 4)])
    roads.remove_road(0, 1)
    roads.add_road(0, 4)
    print(roads.neighbors(0), roads.neighbors(3))
    roads.compact()
    print(roads.neighbors(0), roads.offsets)
