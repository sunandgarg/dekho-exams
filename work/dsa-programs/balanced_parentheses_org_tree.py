class OrganizationParentheses:
    def __init__(self, root_id, children_by_id):
        self.sequence = []
        self.open_at = {}
        self.close_at = {}
        self.parent = {}
        self.labels_at_open = {}
        visited = set()

        def visit(unit_id, parent_id):
            if unit_id in visited:
                raise ValueError("hierarchy must be a tree")
            visited.add(unit_id)
            opening = len(self.sequence)
            self.sequence.append("(")
            self.open_at[unit_id] = opening
            self.labels_at_open[opening] = unit_id
            self.parent[unit_id] = parent_id
            for child_id in children_by_id.get(unit_id, []):
                visit(child_id, unit_id)
            self.close_at[unit_id] = len(self.sequence)
            self.sequence.append(")")

        visit(root_id, None)
        if set(children_by_id) - visited:
            raise ValueError("unreachable hierarchy node")

    def subtree_size(self, unit_id):
        return (self.close_at[unit_id] - self.open_at[unit_id] + 1) // 2

    def contains_descendant(self, ancestor_id, unit_id):
        return (self.open_at[ancestor_id] <= self.open_at[unit_id]
                < self.close_at[unit_id] <= self.close_at[ancestor_id])

    def lowest_common_unit(self, first_id, second_id):
        ancestors = set()
        while first_id is not None:
            ancestors.add(first_id)
            first_id = self.parent[first_id]
        while second_id not in ancestors:
            second_id = self.parent[second_id]
        return second_id


if __name__ == "__main__":
    tree = OrganizationParentheses("operations", {
        "operations": ["dispatch", "quality"],
        "dispatch": ["east", "west"],
        "quality": ["audit"],
    })
    print("encoding:", "".join(tree.sequence))
    print("dispatch subtree:", tree.subtree_size("dispatch"))
    print("east under dispatch:", tree.contains_descendant("dispatch", "east"))
    print("east and audit:", tree.lowest_common_unit("east", "audit"))
