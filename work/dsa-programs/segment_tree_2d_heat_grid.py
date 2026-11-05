class HeatGrid:
    def __init__(self, cells):
        if not cells or not cells[0] or any(len(row) != len(cells[0]) for row in cells):
            raise ValueError("nonempty rectangular grid required")
        self.rows = len(cells)
        self.columns = len(cells[0])
        self.values = [row[:] for row in cells]
        self.row_base = 1 << (self.rows - 1).bit_length()
        self.column_base = 1 << (self.columns - 1).bit_length()
        self.tree = [[0] * (2 * self.column_base) for _ in range(2 * self.row_base)]
        for row_index, row in enumerate(cells):
            for column_index, value in enumerate(row):
                self.tree[self.row_base + row_index][self.column_base + column_index] = value
        for row_node in range(self.row_base, 2 * self.row_base):
            for column_node in range(self.column_base - 1, 0, -1):
                self.tree[row_node][column_node] = (
                    self.tree[row_node][2 * column_node] + self.tree[row_node][2 * column_node + 1]
                )
        for row_node in range(self.row_base - 1, 0, -1):
            for column_node in range(1, 2 * self.column_base):
                self.tree[row_node][column_node] = (
                    self.tree[2 * row_node][column_node] + self.tree[2 * row_node + 1][column_node]
                )

    def replace(self, row_index, column_index, value):
        if not 0 <= row_index < self.rows or not 0 <= column_index < self.columns:
            raise IndexError("grid coordinate")
        self.values[row_index][column_index] = value
        row_node = self.row_base + row_index
        column_leaf = self.column_base + column_index
        while row_node:
            if row_node >= self.row_base:
                self.tree[row_node][column_leaf] = value
            else:
                self.tree[row_node][column_leaf] = (
                    self.tree[2 * row_node][column_leaf] + self.tree[2 * row_node + 1][column_leaf]
                )
            column_node = column_leaf // 2
            while column_node:
                self.tree[row_node][column_node] = (
                    self.tree[row_node][2 * column_node] + self.tree[row_node][2 * column_node + 1]
                )
                column_node //= 2
            row_node //= 2

    def rectangle_sum(self, top, bottom, left, right):
        """Sum cells in [top,bottom) by [left,right)."""
        if not (0 <= top <= bottom <= self.rows and 0 <= left <= right <= self.columns):
            raise ValueError("rectangle outside grid")
        row_left, row_right = top + self.row_base, bottom + self.row_base
        total = 0
        while row_left < row_right:
            if row_left & 1:
                total += self._column_sum(row_left, left, right)
                row_left += 1
            if row_right & 1:
                row_right -= 1
                total += self._column_sum(row_right, left, right)
            row_left //= 2
            row_right //= 2
        return total

    def _column_sum(self, row_node, left, right):
        column_left, column_right = left + self.column_base, right + self.column_base
        total = 0
        while column_left < column_right:
            if column_left & 1:
                total += self.tree[row_node][column_left]
                column_left += 1
            if column_right & 1:
                column_right -= 1
                total += self.tree[row_node][column_right]
            column_left //= 2
            column_right //= 2
        return total


heat_grid = HeatGrid([[19, 47, 29], [61, 83, 17], [23, 31, 53]])
print("upper rectangle:", heat_grid.rectangle_sum(0, 2, 1, 3))
heat_grid.replace(1, 2, 41)
print("after sensor correction:", heat_grid.rectangle_sum(0, 2, 1, 3))
