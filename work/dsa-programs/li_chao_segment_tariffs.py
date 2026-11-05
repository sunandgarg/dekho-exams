class SegmentTariffIndex:
    def __init__(self, first_minute, past_last_minute):
        if first_minute >= past_last_minute:
            raise ValueError("nonempty integer domain required")
        self.start = first_minute
        self.stop = past_last_minute
        self.lines = {}

    @staticmethod
    def _charge(line, minute):
        slope, base = line
        return slope * minute + base

    def _place_line(self, node, low, high, offered):
        incumbent = self.lines.get(node)
        if incumbent is None:
            self.lines[node] = offered
            return
        middle = (low + high) // 2
        if self._charge(offered, middle) < self._charge(incumbent, middle):
            self.lines[node], offered = offered, incumbent
        incumbent = self.lines[node]
        if high - low == 1:
            return
        if self._charge(offered, low) < self._charge(incumbent, low):
            self._place_line(node * 2, low, middle, offered)
        elif self._charge(offered, high - 1) < self._charge(incumbent, high - 1):
            self._place_line(node * 2 + 1, middle, high, offered)

    def add_tariff(self, first_minute, past_last_minute, slope, base):
        if not self.start <= first_minute < past_last_minute <= self.stop:
            raise IndexError("offer interval outside domain")

        def visit(node, low, high):
            if past_last_minute <= low or high <= first_minute:
                return
            if first_minute <= low and high <= past_last_minute:
                self._place_line(node, low, high, (slope, base))
                return
            middle = (low + high) // 2
            visit(node * 2, low, middle)
            visit(node * 2 + 1, middle, high)

        visit(1, self.start, self.stop)

    def minimum_charge(self, minute):
        if not self.start <= minute < self.stop:
            raise IndexError(minute)
        node, low, high = 1, self.start, self.stop
        answer = None
        while True:
            if node in self.lines:
                candidate = self._charge(self.lines[node], minute)
                answer = candidate if answer is None else min(answer, candidate)
            if high - low == 1:
                return answer
            middle = (low + high) // 2
            if minute < middle:
                node, high = node * 2, middle
            else:
                node, low = node * 2 + 1, middle


tariffs = SegmentTariffIndex(0, 16)
tariffs.add_tariff(0, 16, 3, 47)
tariffs.add_tariff(4, 12, -2, 83)
tariffs.add_tariff(9, 16, 1, 29)
print(tariffs.minimum_charge(2), tariffs.minimum_charge(7))
print(tariffs.minimum_charge(10), tariffs.minimum_charge(15))
