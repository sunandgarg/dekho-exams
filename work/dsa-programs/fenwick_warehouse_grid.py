"""Point assignments and half-open rectangular sums on a fixed grid."""


class WarehouseGrid:
    def __init__(self, rows: int, columns: int):
        if rows <= 0 or columns <= 0:
            raise ValueError("grid dimensions must be positive")
        self.rows, self.columns = rows, columns
        self.values = [[0] * columns for _ in range(rows)]
        self.tree = [[0] * (columns + 1) for _ in range(rows + 1)]

    def assign(self, row: int, column: int, quantity: int) -> None:
        if not 0 <= row < self.rows or not 0 <= column < self.columns:
            raise IndexError((row, column))
        difference = quantity - self.values[row][column]
        self.values[row][column] = quantity
        row_index = row + 1
        while row_index <= self.rows:
            column_index = column + 1
            while column_index <= self.columns:
                self.tree[row_index][column_index] += difference
                column_index += column_index & -column_index
            row_index += row_index & -row_index

    def prefix(self, row_stop: int, column_stop: int) -> int:
        if not 0 <= row_stop <= self.rows or not 0 <= column_stop <= self.columns:
            raise IndexError((row_stop, column_stop))
        total = 0
        row_index = row_stop
        while row_index:
            column_index = column_stop
            while column_index:
                total += self.tree[row_index][column_index]
                column_index -= column_index & -column_index
            row_index -= row_index & -row_index
        return total

    def rectangle(self, row_start: int, row_stop: int, column_start: int, column_stop: int) -> int:
        if not 0 <= row_start <= row_stop <= self.rows or not 0 <= column_start <= column_stop <= self.columns:
            raise IndexError((row_start, row_stop, column_start, column_stop))
        return (self.prefix(row_stop, column_stop)
                - self.prefix(row_start, column_stop)
                - self.prefix(row_stop, column_start)
                + self.prefix(row_start, column_start))


warehouse = WarehouseGrid(4, 5)
warehouse.assign(1, 2, 47)
warehouse.assign(2, 3, 61)
warehouse.assign(3, 4, 19)
print(warehouse.rectangle(1, 3, 2, 4))
warehouse.assign(1, 2, 26)
print(warehouse.rectangle(1, 3, 2, 4))
print(warehouse.rectangle(0, 4, 0, 5))
