class DispatchRuleDiagram:
    def __init__(self, variable_order, predicate):
        self.variables = tuple(variable_order)
        if len(set(self.variables)) != len(self.variables):
            raise ValueError("variable names must be unique")
        self.nodes = {}
        self.unique = {}

        def build(level, assignment):
            if level == len(self.variables):
                return int(bool(predicate(assignment)))
            variable = self.variables[level]
            assignment[variable] = False
            low = build(level + 1, assignment)
            assignment[variable] = True
            high = build(level + 1, assignment)
            del assignment[variable]
            if low == high:
                return low
            identity = (variable, low, high)
            if identity not in self.unique:
                node_id = len(self.nodes) + 2
                self.unique[identity] = node_id
                self.nodes[node_id] = identity
            return self.unique[identity]

        self.root = build(0, {})

    def permits(self, flags):
        if set(flags) != set(self.variables):
            raise ValueError("assignment must name every variable once")
        node_id = self.root
        while node_id > 1:
            variable, low, high = self.nodes[node_id]
            node_id = high if flags[variable] else low
        return bool(node_id)


if __name__ == "__main__":
    rule = DispatchRuleDiagram(
        ["override", "paid", "approved"],
        lambda flags: flags["override"] or (flags["paid"] and flags["approved"]),
    )
    print(len(rule.nodes), rule.permits({"override": False, "paid": True, "approved": True}))
    print(rule.permits({"override": False, "paid": True, "approved": False}))
    print(rule.permits({"override": True, "paid": False, "approved": False}))
