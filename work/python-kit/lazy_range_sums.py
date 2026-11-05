class RangeAmounts:
    def __init__(self, amounts):
        if not 1 <= len(amounts) <= 128 or any(type(amount) is not int for amount in amounts):
            raise ValueError("bounded integer amounts required")
        self.count = len(amounts)
        self.sums = [0] * (4 * self.count)
        self.lazy = [0] * (4 * self.count)
        def build(position, left, right):
            if right - left == 1:
                self.sums[position] = amounts[left]
                return
            middle = (left + right) // 2
            build(position * 2, left, middle); build(position * 2 + 1, middle, right)
            self.sums[position] = self.sums[position * 2] + self.sums[position * 2 + 1]
        build(1, 0, self.count)
    def _validate(self, left, right):
        if any(type(index) is not int for index in (left, right)) or not 0 <= left <= right <= self.count:
            raise ValueError("invalid half-open interval")
    def _apply(self, position, length, delta):
        self.sums[position] += length * delta
        self.lazy[position] += delta
    def _push(self, position, left, right):
        if self.lazy[position] and right - left > 1:
            middle = (left + right) // 2
            self._apply(position * 2, middle - left, self.lazy[position])
            self._apply(position * 2 + 1, right - middle, self.lazy[position])
            self.lazy[position] = 0
    def add(self, left, right, delta):
        self._validate(left, right)
        if type(delta) is not int:
            raise ValueError("integer delta required")
        def change(position, start, end):
            if right <= start or end <= left:
                return
            if left <= start and end <= right:
                self._apply(position, end - start, delta)
                return
            self._push(position, start, end)
            middle = (start + end) // 2
            change(position * 2, start, middle); change(position * 2 + 1, middle, end)
            self.sums[position] = self.sums[position * 2] + self.sums[position * 2 + 1]
        if left != right:
            change(1, 0, self.count)
    def total(self, left, right):
        self._validate(left, right)
        def query(position, start, end):
            if right <= start or end <= left:
                return 0
            if left <= start and end <= right:
                return self.sums[position]
            self._push(position, start, end)
            middle = (start + end) // 2
            return query(position * 2, start, middle) + query(position * 2 + 1, middle, end)
        return query(1, 0, self.count) if left != right else 0

ledger = RangeAmounts([1, 3, 5, 7])
print(ledger.total(0, 4))
ledger.add(1, 3, 2)
print(ledger.total(0, 4))
print(ledger.total(2, 3))
print(ledger.total(2, 2))
