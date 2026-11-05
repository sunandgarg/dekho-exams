class ReachabilitySnapshot:
    def __init__(self, vertex_count, directed_edges):
        if vertex_count < 0:
            raise ValueError("negative vertex count")
        self.count = vertex_count
        self.rows = [1 << vertex for vertex in range(vertex_count)]
        for source, target in directed_edges:
            self._check(source)
            self._check(target)
            self.rows[source] |= 1 << target
        for intermediate in range(vertex_count):
            through = self.rows[intermediate]
            for source in range(vertex_count):
                if self.rows[source] & (1 << intermediate):
                    self.rows[source] |= through

    def _check(self, vertex):
        if not 0 <= vertex < self.count:
            raise ValueError("vertex outside graph")

    def reaches(self, source, target):
        self._check(source)
        self._check(target)
        return bool(self.rows[source] & (1 << target))

    def reachable_from(self, source):
        self._check(source)
        row = self.rows[source]
        return [vertex for vertex in range(self.count) if row & (1 << vertex)]


if __name__ == "__main__":
    routes = ReachabilitySnapshot(6, [(0, 1), (1, 2), (2, 0), (2, 4), (4, 5)])
    print(routes.reaches(0, 5), routes.reaches(5, 0))
    print(routes.reachable_from(1))
