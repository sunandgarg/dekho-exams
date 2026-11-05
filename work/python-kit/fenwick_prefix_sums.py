class PrefixLedger:
    def __init__(self, amounts):
        if type(amounts) is not list or not 1 <= len(amounts) <= 100 or any(type(value) is not int or not 0 <= value <= 1000 for value in amounts):
            raise ValueError("bounded amounts")
        self.size = len(amounts)
        self.tree = [0] * (self.size + 1)
        for index, amount in enumerate(amounts):
            self.add(index, amount)
    def add(self, index, delta):
        if type(index) is not int or not 0 <= index < self.size or type(delta) is not int or not -1000 <= delta <= 1000:
            raise ValueError("point update")
        position = index + 1
        while position <= self.size:
            self.tree[position] += delta
            position += position & -position
    def prefix(self, end):
        if type(end) is not int or not 0 <= end <= self.size:
            raise ValueError("exclusive end")
        total = 0
        while end:
            total += self.tree[end]
            end -= end & -end
        return total

ledger = PrefixLedger([125, 75, 50])
print(ledger.prefix(2))
ledger.add(1, 25)
print(ledger.prefix(2), ledger.prefix(3))
