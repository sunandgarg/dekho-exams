from bisect import bisect_left


def morton_code(x, y, bits):
    code = 0
    for position in range(bits):
        code |= ((x >> position) & 1) << (2 * position)
        code |= ((y >> position) & 1) << (2 * position + 1)
    return code


class MortonDepotIndex:
    def __init__(self, points, bits=8):
        if bits < 1 or bits > 16:
            raise ValueError("bits must be between one and sixteen")
        self.bits = bits
        self.width = 1 << bits
        if len({depot_id for depot_id, _, _ in points}) != len(points):
            raise ValueError("duplicate depot ID")
        if any(not (0 <= x < self.width and 0 <= y < self.width)
               for _, x, y in points):
            raise ValueError("point outside integer grid")
        self.records = sorted((morton_code(x, y, bits), depot_id, x, y)
                              for depot_id, x, y in points)
        self.codes = [record[0] for record in self.records]

    def range_report(self, left, bottom, right, top):
        if not (0 <= left <= right <= self.width and
                0 <= bottom <= top <= self.width):
            raise ValueError("invalid query rectangle")
        found = []

        def visit(x0, y0, width, prefix, remaining):
            x1, y1 = x0 + width, y0 + width
            if left >= x1 or right <= x0 or bottom >= y1 or top <= y0:
                return
            if (left <= x0 and x1 <= right and bottom <= y0 and y1 <= top):
                start = bisect_left(self.codes, prefix)
                end = bisect_left(self.codes, prefix + (1 << (2 * remaining)))
                found.extend(record[1] for record in self.records[start:end])
                return
            if remaining == 0:
                return
            half = width // 2
            for quadrant in range(4):
                visit(x0 + (quadrant & 1) * half,
                      y0 + (quadrant >> 1) * half, half,
                      prefix | (quadrant << (2 * (remaining - 1))), remaining - 1)

        visit(0, 0, self.width, 0, self.bits)
        return sorted(found)


index = MortonDepotIndex([
    ("pump-47", 47, 52), ("valve-19", 19, 61),
    ("sensor-61", 52, 58), ("grid-83", 180, 70),
])
print("window=", index.range_report(15, 45, 60, 65), sep="")
