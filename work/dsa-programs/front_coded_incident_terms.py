from bisect import bisect_right


class FrontCodedIncidentTerms:
    def __init__(self, terms, block_size=4):
        if block_size < 1:
            raise ValueError("block size must be positive")
        ordered = sorted(set(terms))
        self.anchors = []
        self.blocks = []
        for start in range(0, len(ordered), block_size):
            group = ordered[start:start + block_size]
            anchor = group[0]
            self.anchors.append(anchor)
            encoded = []
            for term in group[1:]:
                shared = 0
                while shared < min(len(anchor), len(term)) and anchor[shared] == term[shared]:
                    shared += 1
                encoded.append((shared, term[shared:]))
            self.blocks.append(encoded)

    def block_terms(self, block):
        anchor = self.anchors[block]
        return [anchor] + [anchor[:shared] + suffix for shared, suffix in self.blocks[block]]

    def contains(self, term):
        block = bisect_right(self.anchors, term) - 1
        return block >= 0 and term in self.block_terms(block)


if __name__ == "__main__":
    lexicon = FrontCodedIncidentTerms([
        "pressure", "pressurized", "pressurize", "pump", "pumps", "valve", "valves"
    ], block_size=3)
    print("first-block=", lexicon.block_terms(0), sep="")
    print("pressurized=", lexicon.contains("pressurized"), sep="")
    print("pressurizer=", lexicon.contains("pressurizer"), sep="")
