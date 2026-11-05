from functools import total_ordering

@total_ordering
class ReceiptRank:
    def __init__(self, priority):
        if type(priority) is not int or not 0 <= priority <= 9:
            raise ValueError("priority bound")
        self.priority = priority
    def __eq__(self, other):
        if type(other) is not ReceiptRank:
            return NotImplemented
        return self.priority == other.priority
    def __lt__(self, other):
        if type(other) is not ReceiptRank:
            return NotImplemented
        return self.priority < other.priority

print("ordered:", ReceiptRank(2) < ReceiptRank(4))
print("unrelated equal:", ReceiptRank(2) == 2)
print("method fallback:", ReceiptRank(2).__lt__(2) is NotImplemented)
try:
    ReceiptRank(2) < 2
except TypeError:
    print("unrelated ordering rejected")
