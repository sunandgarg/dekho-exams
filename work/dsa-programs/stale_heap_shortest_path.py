from heapq import heappop, heappush


def shortest_route(roads, origin, destination):
    if origin not in roads or destination not in roads:
        raise ValueError("unknown depot")
    for departures in roads.values():
        for neighbor, travel_minutes in departures:
            if neighbor not in roads or travel_minutes < 0:
                raise ValueError("unknown depot or negative travel time")

    best = {origin: 0}
    previous = {}
    pending = [(0, origin)]
    while pending:
        distance, depot = heappop(pending)
        if distance != best[depot]:
            continue
        if depot == destination:
            route = [depot]
            while route[-1] != origin:
                route.append(previous[route[-1]])
            return distance, list(reversed(route))
        for neighbor, travel_minutes in roads[depot]:
            candidate = distance + travel_minutes
            if candidate < best.get(neighbor, float("inf")):
                best[neighbor] = candidate
                previous[neighbor] = depot
                heappush(pending, (candidate, neighbor))
    return None


depot_roads = {
    "D-19": [("D-26", 7), ("D-47", 14)],
    "D-26": [("D-47", 3), ("D-52", 8)],
    "D-47": [("D-52", 4)],
    "D-52": [],
}
print(shortest_route(depot_roads, "D-19", "D-52"))
print(shortest_route(depot_roads, "D-52", "D-19"))
