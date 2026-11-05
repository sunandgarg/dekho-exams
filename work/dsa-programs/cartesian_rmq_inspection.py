class CartesianReadingIndex:
    def __init__(self, readings):
        self.readings = list(readings)
        count = len(readings)
        self.parent = [None] * count
        self.left = [None] * count
        self.right = [None] * count
        stack = []
        for index, value in enumerate(readings):
            displaced = None
            while stack and (value, index) < (readings[stack[-1]], stack[-1]):
                displaced = stack.pop()
            if stack:
                self.right[stack[-1]] = index
                self.parent[index] = stack[-1]
            if displaced is not None:
                self.left[index] = displaced
                self.parent[displaced] = index
            stack.append(index)
        self.root = stack[0] if stack else None

    def minimum(self, first, last):
        if not 0 <= first <= last < len(self.readings):
            raise IndexError("invalid inclusive reading range")
        ancestors = set()
        cursor = first
        while cursor is not None:
            ancestors.add(cursor)
            cursor = self.parent[cursor]
        cursor = last
        while cursor not in ancestors:
            cursor = self.parent[cursor]
        return self.readings[cursor], cursor


index = CartesianReadingIndex([47, 19, 19, 61, 29, 83])
print(index.root, index.minimum(1, 4), index.minimum(3, 5))
