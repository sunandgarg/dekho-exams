class TournamentMerge:
    def __init__(self, sorted_runs):
        self.runs = [list(run) for run in sorted_runs]
        if any(run != sorted(run) for run in self.runs):
            raise ValueError("each input run must be sorted")
        self.count = len(self.runs)
        self.base = 1
        while self.base < max(1, self.count):
            self.base *= 2
        self.positions = [0] * self.count
        self.winners = [None] * (2 * self.base)
        for run_id, run in enumerate(self.runs):
            if run:
                self.winners[self.base + run_id] = run_id
        for position in range(self.base - 1, 0, -1):
            self.winners[position] = self._better(self.winners[2 * position], self.winners[2 * position + 1])

    def _better(self, first, second):
        if first is None:
            return second
        if second is None:
            return first
        first_key = (self.runs[first][self.positions[first]], first)
        second_key = (self.runs[second][self.positions[second]], second)
        return first if first_key <= second_key else second

    def pop(self):
        winner = self.winners[1]
        if winner is None:
            raise IndexError("all runs exhausted")
        value = self.runs[winner][self.positions[winner]]
        self.positions[winner] += 1
        leaf = self.base + winner
        if self.positions[winner] == len(self.runs[winner]):
            self.winners[leaf] = None
        while leaf > 1:
            leaf //= 2
            self.winners[leaf] = self._better(self.winners[2 * leaf], self.winners[2 * leaf + 1])
        return value, winner

    def drain(self):
        merged = []
        while self.winners[1] is not None:
            merged.append(self.pop())
        return merged


if __name__ == "__main__":
    merge = TournamentMerge([[19, 47, 83], [29, 47, 61], [], [17, 103]])
    print(merge.drain())
