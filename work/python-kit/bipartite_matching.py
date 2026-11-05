def maximum_assignment(allowed, slot_count):
    if type(allowed) is not list or len(allowed) > 8 or type(slot_count) is not int or not 0 <= slot_count <= 8:
        raise ValueError("roster bounds")
    for row in allowed:
        if type(row) is not list or any(type(slot) is not int or not 0 <= slot < slot_count for slot in row) or len(set(row)) != len(row):
            raise ValueError("slot endpoints")
    owners = [-1] * slot_count
    def augment(worker, visited):
        for slot in allowed[worker]:
            if slot in visited:
                continue
            visited.add(slot)
            if owners[slot] == -1 or augment(owners[slot], visited):
                owners[slot] = worker
                return True
        return False
    for worker in range(len(allowed)):
        augment(worker, set())
    return sorted((worker, slot) for slot, worker in enumerate(owners) if worker != -1)

print("pairs:", maximum_assignment([[0, 1], [0]], 2))
print("isolated:", maximum_assignment([[], [1]], 2))
print("empty:", maximum_assignment([], 0))
try:
    maximum_assignment([[True]], 2)
except ValueError:
    print("Boolean endpoint rejected")
