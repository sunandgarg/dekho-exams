class IncidentFMIndex:
    def __init__(self, text):
        if "\0" in text:
            raise ValueError("sentinel may not appear in text")
        self.text_length = len(text)
        indexed = text + "\0"
        self.suffix_positions = sorted(range(len(indexed)), key=lambda position: indexed[position:])
        self.last_column = "".join(indexed[position - 1] for position in self.suffix_positions)
        alphabet = sorted(set(indexed))
        frequencies = {letter: indexed.count(letter) for letter in alphabet}
        self.first_offset = {}
        running = 0
        for letter in alphabet:
            self.first_offset[letter] = running
            running += frequencies[letter]
        self.rank = {}
        for letter in alphabet:
            counts = [0]
            for observed in self.last_column:
                counts.append(counts[-1] + (observed == letter))
            self.rank[letter] = counts

    def _matching_suffix_interval(self, pattern):
        if not pattern or "\0" in pattern:
            raise ValueError("pattern must be nonempty and exclude the sentinel")
        left, right = 0, len(self.suffix_positions)
        for letter in reversed(pattern):
            if letter not in self.first_offset:
                return 0, 0
            left = self.first_offset[letter] + self.rank[letter][left]
            right = self.first_offset[letter] + self.rank[letter][right]
            if left == right:
                break
        return left, right

    def count(self, pattern):
        left, right = self._matching_suffix_interval(pattern)
        return right - left

    def positions(self, pattern):
        left, right = self._matching_suffix_interval(pattern)
        return sorted(position for position in self.suffix_positions[left:right]
                      if position < self.text_length)


if __name__ == "__main__":
    index = IncidentFMIndex("cabacaba")
    print("aba count:", index.count("aba"))
    print("aba positions:", index.positions("aba"))
    print("xyz count:", index.count("xyz"))
