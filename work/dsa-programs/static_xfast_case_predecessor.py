class StaticXFastCases:
    def __init__(self, case_ids, bit_width):
        if bit_width < 1:
            raise ValueError("bit width must be positive")
        ordered = sorted(set(case_ids))
        if any(key < 0 or key >= 1 << bit_width for key in ordered):
            raise ValueError("case ID outside universe")
        self.width = bit_width
        self.levels = [dict() for _ in range(bit_width + 1)]
        self.previous = {}
        self.next = {}
        for position, key in enumerate(ordered):
            self.previous[key] = ordered[position - 1] if position else None
            self.next[key] = ordered[position + 1] if position + 1 < len(ordered) else None
            for length in range(bit_width + 1):
                prefix = key >> (bit_width - length)
                low, high = self.levels[length].get(prefix, (key, key))
                self.levels[length][prefix] = min(low, key), max(high, key)

    def floor(self, target):
        if target < 0 or target >= 1 << self.width:
            raise ValueError("target outside universe")
        if not self.previous:
            return None
        if target in self.previous:
            return target
        low, high = 0, self.width
        while low + 1 < high:
            middle = (low + high) // 2
            prefix = target >> (self.width - middle)
            if prefix in self.levels[middle]:
                low = middle
            else:
                high = middle
        prefix = target >> (self.width - low)
        smallest, largest = self.levels[low][prefix]
        missing_bit = (target >> (self.width - low - 1)) & 1
        return largest if missing_bit else self.previous[smallest]

    def ceiling(self, target):
        if target < 0 or target >= 1 << self.width:
            raise ValueError("target outside universe")
        if not self.next:
            return None
        if target in self.next:
            return target
        low, high = 0, self.width
        while low + 1 < high:
            middle = (low + high) // 2
            prefix = target >> (self.width - middle)
            if prefix in self.levels[middle]:
                low = middle
            else:
                high = middle
        prefix = target >> (self.width - low)
        smallest, largest = self.levels[low][prefix]
        missing_bit = (target >> (self.width - low - 1)) & 1
        return self.next[largest] if missing_bit else smallest


if __name__ == "__main__":
    catalog = StaticXFastCases([19, 47, 83, 149], 8)
    print(catalog.floor(61), catalog.ceiling(61))
    print(catalog.floor(19), catalog.ceiling(149))
    print(catalog.floor(7), catalog.ceiling(201))
