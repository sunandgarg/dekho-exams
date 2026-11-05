"""Prefix-doubling suffix array, linear LCP pass, and substring lookup."""


class IncidentTextIndex:
    def __init__(self, incident_text):
        self.text = incident_text
        length = len(incident_text)
        self.suffixes = list(range(length))
        if not length:
            self.lcp = []
            return

        ranks = [ord(character) for character in incident_text]
        width = 1
        while True:
            self.suffixes.sort(key=lambda start: (ranks[start], ranks[start + width] if start + width < length else -1))
            next_ranks = [0] * length
            for offset in range(1, length):
                previous = self.suffixes[offset - 1]
                current = self.suffixes[offset]
                previous_pair = (ranks[previous], ranks[previous + width] if previous + width < length else -1)
                current_pair = (ranks[current], ranks[current + width] if current + width < length else -1)
                next_ranks[current] = next_ranks[previous] + (previous_pair != current_pair)
            ranks = next_ranks
            if ranks[self.suffixes[-1]] == length - 1:
                break
            width *= 2

        order = [0] * length
        for rank, start in enumerate(self.suffixes):
            order[start] = rank
        self.lcp = [0] * length
        matched = 0
        for start in range(length):
            rank = order[start]
            if rank == 0:
                continue
            predecessor = self.suffixes[rank - 1]
            while start + matched < length and predecessor + matched < length and incident_text[start + matched] == incident_text[predecessor + matched]:
                matched += 1
            self.lcp[rank] = matched
            if matched:
                matched -= 1

    def occurrences(self, pattern):
        if not pattern:
            raise ValueError("empty pattern has no indexed search contract")
        size = len(self.suffixes)

        def boundary(upper):
            low, high = 0, size
            while low < high:
                middle = (low + high) // 2
                prefix = self.text[self.suffixes[middle]:self.suffixes[middle] + len(pattern)]
                if prefix < pattern or (upper and prefix == pattern):
                    low = middle + 1
                else:
                    high = middle
            return low

        return self.suffixes[boundary(False):boundary(True)]


index = IncidentTextIndex("valve alert valve")
print(index.occurrences("valve"))
print(index.occurrences("alert"))
print(index.lcp[index.suffixes.index(0)])
