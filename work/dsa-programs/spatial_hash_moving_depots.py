import math


class MovingDepotGrid:
    def __init__(self, cell_size):
        if cell_size <= 0:
            raise ValueError("cell size must be positive")
        self.cell_size = cell_size
        self.points = {}
        self.cells = {}

    def _cell(self, x, y):
        return math.floor(x / self.cell_size), math.floor(y / self.cell_size)

    def upsert(self, depot_id, x, y):
        destination = self._cell(x, y)
        if depot_id in self.points:
            previous = self._cell(*self.points[depot_id])
            if previous != destination:
                self.cells[previous].remove(depot_id)
                if not self.cells[previous]:
                    del self.cells[previous]
        self.points[depot_id] = (x, y)
        self.cells.setdefault(destination, set()).add(depot_id)

    def remove(self, depot_id):
        x, y = self.points.pop(depot_id)
        cell = self._cell(x, y)
        self.cells[cell].remove(depot_id)
        if not self.cells[cell]:
            del self.cells[cell]

    def within_radius(self, x, y, radius):
        if radius < 0:
            raise ValueError("radius cannot be negative")
        left, bottom = self._cell(x - radius, y - radius)
        right, top = self._cell(x + radius, y + radius)
        matches = []
        for cell_x in range(left, right + 1):
            for cell_y in range(bottom, top + 1):
                for depot_id in self.cells.get((cell_x, cell_y), ()):
                    depot_x, depot_y = self.points[depot_id]
                    if (depot_x - x) ** 2 + (depot_y - y) ** 2 <= radius ** 2:
                        matches.append(depot_id)
        return sorted(matches)


index = MovingDepotGrid(cell_size=8)
index.upsert("pump-47", -3, 4)
index.upsert("valve-19", 9, 5)
index.upsert("sensor-61", 2, 7)
index.upsert("valve-19", 1, 6)
print("near=", index.within_radius(0, 5, 4), "cells=", len(index.cells), sep="")
