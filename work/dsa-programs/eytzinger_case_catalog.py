class EytzingerCaseCatalog:
    def __init__(self, case_ids):
        ordered = sorted(set(case_ids))
        self.layout = [None] * len(ordered)
        self.ranks = [None] * len(ordered)
        cursor = 0

        def place(index):
            nonlocal cursor
            if index >= len(ordered):
                return
            place(2 * index + 1)
            self.layout[index] = ordered[cursor]
            self.ranks[index] = cursor
            cursor += 1
            place(2 * index + 2)

        place(0)

    def lower_bound(self, case_id):
        index, best = 0, None
        while index < len(self.layout):
            if self.layout[index] >= case_id:
                best = index
                index = 2 * index + 1
            else:
                index = 2 * index + 2
        return None if best is None else (self.layout[best], self.ranks[best])

    def contains(self, case_id):
        result = self.lower_bound(case_id)
        return result is not None and result[0] == case_id


catalog = EytzingerCaseCatalog([83, 19, 61, 47, 19, 103, 29])
print(catalog.layout)
print(catalog.lower_bound(52), catalog.contains(61), catalog.lower_bound(104))
