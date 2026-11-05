from collections import deque


def execution_order(requirements):
    successors = {task: [] for task in requirements}
    incoming = {task: 0 for task in requirements}
    for task, prerequisites in requirements.items():
        for prerequisite in dict.fromkeys(prerequisites):
            if prerequisite not in requirements:
                raise ValueError(f"unknown prerequisite: {prerequisite}")
            successors[prerequisite].append(task)
            incoming[task] += 1

    ready = deque(task for task in requirements if incoming[task] == 0)
    order = []
    while ready:
        task = ready.popleft()
        order.append(task)
        for dependent in successors[task]:
            incoming[dependent] -= 1
            if incoming[dependent] == 0:
                ready.append(dependent)
    if len(order) != len(requirements):
        raise ValueError("dependency cycle")
    return order


warehouse_jobs = {
    "stock": [],
    "reserve": ["stock"],
    "pick": ["reserve"],
    "pack": ["pick"],
    "label": ["reserve"],
    "ship": ["pack", "label"],
}
print(execution_order(warehouse_jobs))
try:
    execution_order({"receive": ["audit"], "audit": ["receive"]})
except ValueError as error:
    print(str(error))
