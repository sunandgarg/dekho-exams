from bisect import bisect_right

def best_schedule(jobs):
    if type(jobs) is not list or len(jobs) > 16:
        raise ValueError("job capacity")
    for job in jobs:
        if type(job) is not tuple or len(job) != 3 or any(type(value) is not int or not 0 <= value <= 1000 for value in job) or job[0] >= job[1]:
            raise ValueError("job fields")
    ordered = sorted((end, start, reward, index) for index, (start, end, reward) in enumerate(jobs))
    ends = [job[0] for job in ordered]
    best, previous, take = [0], [], []
    for position, (end, start, reward, identifier) in enumerate(ordered):
        prefix = bisect_right(ends, start, 0, position)
        candidate = best[prefix] + reward
        previous.append(prefix)
        take.append(candidate > best[-1])
        best.append(max(best[-1], candidate))
    chosen = []
    position = len(ordered)
    while position:
        if take[position - 1]:
            chosen.append(ordered[position - 1][3])
            position = previous[position - 1]
        else:
            position -= 1
    return best[-1], list(reversed(chosen))

print("schedule:", best_schedule([(0, 4, 5), (1, 3, 4), (3, 5, 4), (4, 6, 5)]))
print("empty:", best_schedule([]))
try:
    best_schedule([(2, 2, 10)])
except ValueError:
    print("empty duration rejected")
