from heapq import heappop, heappush

def grid_cost(width, height, blocked, start, goal):
    if type(width) is not int or type(height) is not int or not 1 <= width <= 10 or not 1 <= height <= 10 or type(blocked) is not set or any(type(cell) is not tuple or len(cell) != 2 or any(type(value) is not int for value in cell) for cell in blocked) or any(type(cell) is not tuple or len(cell) != 2 or any(type(value) is not int for value in cell) for cell in (start, goal)):
        raise ValueError("grid bounds")
    valid = lambda cell: 0 <= cell[0] < width and 0 <= cell[1] < height and cell not in blocked
    if not valid(start) or not valid(goal):
        raise ValueError("endpoint")
    estimate = lambda cell: abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])
    best = {start: 0}
    frontier = [(estimate(start), 0, start)]
    while frontier:
        _, cost, cell = heappop(frontier)
        if cost != best[cell]:
            continue
        if cell == goal:
            return cost
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (cell[0] + dx, cell[1] + dy)
            if valid(neighbor) and cost + 1 < best.get(neighbor, float("inf")):
                best[neighbor] = cost + 1
                heappush(frontier, (cost + 1 + estimate(neighbor), cost + 1, neighbor))
    return None

print(grid_cost(3, 3, {(1, 1)}, (0, 0), (2, 2)))
print(grid_cost(2, 1, {(1, 0)}, (0, 0), (0, 0)))
