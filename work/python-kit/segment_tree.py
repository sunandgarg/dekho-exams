class LedgerSums:
    def __init__(self, amounts):
        if not 1 <= len(amounts) <= 128 or any(type(amount) is not int for amount in amounts):
            raise ValueError("bounded integer amounts required")
        self.count = len(amounts)
        self.tree = [0] * (2 * self.count)
        self.tree[self.count:] = amounts
        for index in range(self.count - 1, 0, -1):
            self.tree[index] = self.tree[2 * index] + self.tree[2 * index + 1]
    def replace(self, index, amount):
        if type(index) is not int or not 0 <= index < self.count or type(amount) is not int:
            raise ValueError("invalid replacement")
        position = index + self.count
        self.tree[position] = amount
        while position > 1:
            position //= 2
            self.tree[position] = self.tree[2 * position] + self.tree[2 * position + 1]
    def total(self, left, right):
        if any(type(index) is not int for index in (left, right)) or not 0 <= left <= right <= self.count:
            raise ValueError("invalid half-open interval")
        left += self.count
        right += self.count
        amount = 0
        while left < right:
            if left % 2:
                amount += self.tree[left]
                left += 1
            if right % 2:
                right -= 1
                amount += self.tree[right]
            left //= 2
            right //= 2
        return amount

ledger = LedgerSums([125, 250, 75, 50])
print(ledger.total(1, 4))
ledger.replace(2, 100)
print(ledger.total(0, 4))
print(ledger.total(2, 2))
