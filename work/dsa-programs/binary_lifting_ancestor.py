"""Static rooted-tree ancestors and lowest common ancestors."""


class ReportingTree:
    def __init__(self, employee_ids: list[str], reports_to: dict[str, str]):
        if not employee_ids or len(employee_ids) != len(set(employee_ids)):
            raise ValueError("employee IDs must be distinct and nonempty")
        self.index = {employee_id: position for position, employee_id in enumerate(employee_ids)}
        if len(reports_to) != len(employee_ids) - 1:
            raise ValueError("one manager relation is required per non-root employee")
        children = [[] for _ in employee_ids]
        child_ids = set()
        for child_id, manager_id in reports_to.items():
            child, manager = self.index[child_id], self.index[manager_id]
            if child == manager or child in child_ids:
                raise ValueError("invalid manager relation")
            child_ids.add(child)
            children[manager].append(child)
        roots = set(range(len(employee_ids))) - child_ids
        if len(roots) != 1:
            raise ValueError("reporting structure needs exactly one root")
        root = roots.pop()
        self.depth = [0] * len(employee_ids)
        parent = [-1] * len(employee_ids)
        visited = {root}
        pending = [root]
        while pending:
            manager = pending.pop()
            for child in children[manager]:
                if child in visited:
                    raise ValueError("reporting structure has a cycle")
                visited.add(child)
                parent[child] = manager
                self.depth[child] = self.depth[manager] + 1
                pending.append(child)
        if len(visited) != len(employee_ids):
            raise ValueError("reporting structure is disconnected")
        self.employee_ids = employee_ids
        self.up = [parent]
        for _ in range(1, len(employee_ids).bit_length()):
            previous = self.up[-1]
            self.up.append([previous[ancestor] if ancestor < 0 else previous[previous[ancestor]] for ancestor in range(len(employee_ids))])

    def ancestor(self, employee_id: str, generations: int) -> str | None:
        if generations < 0:
            raise ValueError("generations must be nonnegative")
        vertex = self.index[employee_id]
        if generations > self.depth[vertex]:
            return None
        bit = 0
        while generations:
            if generations & 1:
                vertex = self.up[bit][vertex]
            generations >>= 1
            bit += 1
        return self.employee_ids[vertex]

    def common_manager(self, first_id: str, second_id: str) -> str:
        left, right = self.index[first_id], self.index[second_id]
        if self.depth[left] < self.depth[right]:
            left, right = right, left
        difference = self.depth[left] - self.depth[right]
        for bit in range(len(self.up)):
            if difference & (1 << bit):
                left = self.up[bit][left]
        if left == right:
            return self.employee_ids[left]
        for bit in range(len(self.up) - 1, -1, -1):
            if self.up[bit][left] != self.up[bit][right]:
                left, right = self.up[bit][left], self.up[bit][right]
        return self.employee_ids[self.up[0][left]]


reporting = ReportingTree(
    ["E-19", "E-26", "E-47", "E-52", "E-61", "E-83"],
    {"E-26": "E-19", "E-47": "E-19", "E-52": "E-26", "E-61": "E-26", "E-83": "E-47"},
)
print(reporting.ancestor("E-52", 2))
print(reporting.common_manager("E-52", "E-61"))
print(reporting.common_manager("E-52", "E-83"))
