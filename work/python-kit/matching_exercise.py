def valid_assignment(allowed, slot_count, pairs):
    if type(allowed) is not list or len(allowed) > 8 or type(slot_count) is not int or not 0 <= slot_count <= 8 or type(pairs) is not list or len(pairs) > 8:
        raise ValueError("assignment bounds")
    for row in allowed:
        if type(row) is not list or any(type(slot) is not int or not 0 <= slot < slot_count for slot in row) or len(set(row)) != len(row):
            raise ValueError("eligibility fields")
    workers, slots = set(), set()
    for pair in pairs:
        if type(pair) is not tuple or len(pair) != 2:
            return False
        worker, slot = pair
        if type(worker) is not int or type(slot) is not int or not 0 <= worker < len(allowed) or slot not in allowed[worker] or worker in workers or slot in slots:
            return False
        workers.add(worker)
        slots.add(slot)
    return True

allowed = [[0, 1], [0]]
for proposal in ([(0, 1), (1, 0)], [(0, 0), (1, 0)], [(1, 1)], []):
    print("feasible:", valid_assignment(allowed, 2, proposal))
