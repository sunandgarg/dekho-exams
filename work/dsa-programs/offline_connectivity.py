class RollbackConnectivity:
    def __init__(self, depot_ids):
        self.parent = {depot_id: depot_id for depot_id in depot_ids}
        self.size = {depot_id: 1 for depot_id in depot_ids}
        self.history = []

    def find(self, depot_id):
        current = depot_id
        while self.parent[current] != current:
            current = self.parent[current]
        return current

    def connected(self, first_depot, second_depot):
        return self.find(first_depot) == self.find(second_depot)

    def join(self, first_depot, second_depot):
        first_root = self.find(first_depot)
        second_root = self.find(second_depot)
        if first_root == second_root:
            return False
        if self.size[first_root] < self.size[second_root]:
            first_root, second_root = second_root, first_root
        self.history.append((second_root, first_root, self.size[first_root]))
        self.parent[second_root] = first_root
        self.size[first_root] += self.size[second_root]
        return True

    def checkpoint(self):
        return len(self.history)

    def rollback(self, checkpoint):
        if checkpoint < 0 or checkpoint > len(self.history):
            raise ValueError("checkpoint outside active history")
        while len(self.history) > checkpoint:
            child, root, old_size = self.history.pop()
            self.parent[child] = child
            self.size[root] = old_size


def answer_timeline(depot_ids, events):
    depot_ids = tuple(depot_ids)
    known = set(depot_ids)
    if len(known) != len(depot_ids):
        raise ValueError("duplicate depot ID")
    if not events:
        return []
    active_since = {}
    intervals = []
    for time, (action, first, second) in enumerate(events):
        if first not in known or second not in known or first == second:
            raise ValueError("unknown or repeated depot")
        if action not in {"add", "remove", "ask"}:
            raise ValueError("unknown action")
        edge = tuple(sorted((first, second)))
        if action == "add":
            if edge in active_since:
                raise ValueError("edge already active")
            active_since[edge] = time
        elif action == "remove":
            if edge not in active_since:
                raise ValueError("edge not active")
            intervals.append((active_since.pop(edge), time, edge))
    for edge, start in active_since.items():
        intervals.append((start, len(events), edge))

    buckets = [[] for _ in range(4 * len(events))]

    def assign(node, left, right, start, stop, edge):
        if start <= left and right <= stop:
            buckets[node].append(edge)
            return
        middle = (left + right) // 2
        if start < middle:
            assign(2 * node, left, middle, start, stop, edge)
        if stop > middle:
            assign(2 * node + 1, middle, right, start, stop, edge)

    for start, stop, edge in intervals:
        assign(1, 0, len(events), start, stop, edge)

    network = RollbackConnectivity(depot_ids)
    answers = []

    def visit(node, left, right):
        checkpoint = network.checkpoint()
        for first, second in buckets[node]:
            network.join(first, second)
        if right - left == 1:
            action, first, second = events[left]
            if action == "ask":
                answers.append(network.connected(first, second))
        else:
            middle = (left + right) // 2
            visit(2 * node, left, middle)
            visit(2 * node + 1, middle, right)
        network.rollback(checkpoint)

    visit(1, 0, len(events))
    return answers


changes = [
    ("add", "D-19", "D-26"),
    ("ask", "D-19", "D-47"),
    ("add", "D-26", "D-47"),
    ("ask", "D-19", "D-47"),
    ("remove", "D-26", "D-47"),
    ("ask", "D-19", "D-47"),
]
print(answer_timeline(("D-19", "D-26", "D-47"), changes))
