class DispatchSetFamily:
    """Static zero-suppressed diagram for subsets of an ordered item universe."""

    def __init__(self, ordered_items, allowed_sets):
        self.items = tuple(ordered_items)
        if len(set(self.items)) != len(self.items):
            raise ValueError("duplicate universe item")
        universe = set(self.items)
        family = {frozenset(subset) for subset in allowed_sets}
        if any(not subset <= universe for subset in family):
            raise ValueError("set contains an unknown item")
        self.nodes = {0: None, 1: None}  # Empty family and family containing empty set.
        self.unique = {}

        def build(level, subsets):
            if not subsets:
                return 0
            if level == len(self.items):
                return 1
            item = self.items[level]
            low_sets = frozenset(subset for subset in subsets if item not in subset)
            high_sets = frozenset(subset - {item} for subset in subsets if item in subset)
            low = build(level + 1, low_sets)
            high = build(level + 1, high_sets)
            if high == 0:
                return low
            key = (level, low, high)
            if key not in self.unique:
                node_id = len(self.nodes)
                self.unique[key] = node_id
                self.nodes[node_id] = key
            return self.unique[key]

        self.root = build(0, frozenset(family))

    def contains(self, selected_items):
        selected = set(selected_items)
        if not selected <= set(self.items):
            raise ValueError("set contains an unknown item")
        node = self.root
        previous_level = -1
        while node > 1:
            level, low, high = self.nodes[node]
            if any(self.items[skipped] in selected for skipped in range(previous_level + 1, level)):
                return False
            item = self.items[level]
            if item in selected:
                selected.remove(item)
                node = high
            else:
                node = low
            previous_level = level
        return node == 1 and not selected

    def family_size(self):
        cache = {0: 0, 1: 1}

        def count(node):
            if node not in cache:
                _, low, high = self.nodes[node]
                cache[node] = count(low) + count(high)
            return cache[node]

        return count(self.root)


dispatch_families = DispatchSetFamily(
    ("cold", "fragile", "insured", "oversized"),
    ({"cold", "insured"}, {"fragile", "insured"}, {"insured"}, {"cold", "fragile", "insured"}),
)
print("family size:", dispatch_families.family_size())
print("cold insured:", dispatch_families.contains({"cold", "insured"}))
print("cold alone:", dispatch_families.contains({"cold"}))
print("internal nodes:", len(dispatch_families.nodes) - 2)
