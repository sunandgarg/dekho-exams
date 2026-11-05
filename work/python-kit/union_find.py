class ReceiptGroups:
    def __init__(self, count):
        if type(count) is not int or not 0 <= count <= 128:
            raise ValueError("group budget")
        self.parent = list(range(count))
        self.size = [1] * count
        self.groups = count
    def find(self, member):
        if type(member) is not int or not 0 <= member < len(self.parent):
            raise ValueError("member index")
        while member != self.parent[member]:
            self.parent[member] = self.parent[self.parent[member]]
            member = self.parent[member]
        return member
    def union(self, first, second):
        left, right = self.find(first), self.find(second)
        if left == right:
            return False
        if self.size[left] < self.size[right]:
            left, right = right, left
        self.parent[right] = left
        self.size[left] += self.size[right]
        self.groups -= 1
        return True

groups = ReceiptGroups(4)
print(groups.union(0, 1), groups.union(1, 2), groups.union(0, 2))
print(groups.find(0) == groups.find(2), groups.groups)
