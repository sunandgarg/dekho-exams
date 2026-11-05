def travel_metric(first, second):
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


class DepotVantageTree:
    def __init__(self, depots):
        if len({depot_id for depot_id, _ in depots}) != len(depots):
            raise ValueError("depot IDs must be unique")
        self.root = self._build(list(depots))

    def _build(self, depots):
        if not depots:
            return None
        pivot_id, pivot_point = depots[0]
        remaining = sorted(((travel_metric(pivot_point, point), depot_id, point)
                            for depot_id, point in depots[1:]))
        middle = len(remaining) // 2
        radius = remaining[middle][0] if remaining else 0
        return {"id": pivot_id, "point": pivot_point, "radius": radius,
                "near": self._build([(depot_id, point) for _, depot_id, point in remaining[:middle]]),
                "far": self._build([(depot_id, point) for _, depot_id, point in remaining[middle:]])}

    def nearest(self, destination):
        best = None

        def visit(node):
            nonlocal best
            if node is None:
                return
            distance = travel_metric(destination, node["point"])
            candidate = (distance, node["id"])
            if best is None or candidate < best:
                best = candidate
            near_first = distance < node["radius"]
            first = node["near"] if near_first else node["far"]
            second = node["far"] if near_first else node["near"]
            visit(first)
            if second is not None and abs(distance - node["radius"]) <= best[0]:
                visit(second)

        visit(self.root)
        return None if best is None else (best[1], best[0])


if __name__ == "__main__":
    depots = DepotVantageTree([
        ("east", (19, 47)), ("west", (83, 29)), ("north", (47, 61)),
        ("south", (29, 19)), ("central", (47, 47)),
    ])
    print("nearest to (50,45):", depots.nearest((50, 45)))
    print("nearest to (80,30):", depots.nearest((80, 30)))
