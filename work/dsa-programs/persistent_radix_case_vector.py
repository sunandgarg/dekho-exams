BRANCH = 4


def replace_path(node, height, index, value):
    children = list(node)
    slot = (index // (BRANCH ** height)) % BRANCH
    while len(children) <= slot:
        children.append(None)
    if height == 0:
        children[slot] = value
    else:
        children[slot] = replace_path(children[slot] or (), height - 1, index, value)
    return tuple(children)


class CaseVector:
    def __init__(self, root=(), height=0, length=0):
        self.root, self.height, self.length = root, height, length

    def at(self, index):
        if not 0 <= index < self.length:
            raise IndexError(index)
        node = self.root
        for height in range(self.height, -1, -1):
            node = node[(index // (BRANCH ** height)) % BRANCH]
        return node

    def replace(self, index, value):
        if not 0 <= index < self.length:
            raise IndexError(index)
        return CaseVector(replace_path(self.root, self.height, index, value), self.height, self.length)

    def append(self, value):
        root, height = self.root, self.height
        if self.length == BRANCH ** (height + 1):
            root, height = (root,), height + 1
        return CaseVector(replace_path(root, height, self.length, value), height, self.length + 1)

    def values(self):
        return [self.at(index) for index in range(self.length)]


if __name__ == "__main__":
    morning = CaseVector()
    for case_id in [19, 47, 83, 149, 173]:
        morning = morning.append(case_id)
    corrected = morning.replace(2, 103)
    evening = corrected.append(211)
    print(morning.values())
    print(corrected.values())
    print(evening.values())
