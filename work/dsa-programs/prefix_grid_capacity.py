class CapacityGridPrefix:
    def __init__(self, capacity_rows):
        self.rows = len(capacity_rows)
        self.columns = len(capacity_rows[0]) if self.rows else 0
        if any(len(row) != self.columns for row in capacity_rows):
            raise ValueError("capacity grid must be rectangular")
        self.prefix = [[0] * (self.columns + 1) for _ in range(self.rows + 1)]
        for row in range(self.rows):
            for column in range(self.columns):
                self.prefix[row + 1][column + 1] = (
                    capacity_rows[row][column]
                    + self.prefix[row][column + 1]
                    + self.prefix[row + 1][column]
                    - self.prefix[row][column]
                )

    def rectangle_sum(self, top, left, bottom, right):
        if not 0 <= top <= bottom <= self.rows or not 0 <= left <= right <= self.columns:
            raise IndexError("invalid half-open rectangle")
        return (
            self.prefix[bottom][right]
            - self.prefix[top][right]
            - self.prefix[bottom][left]
            + self.prefix[top][left]
        )


if __name__ == "__main__":
    grid = CapacityGridPrefix([[23, 47, 19, 61], [38, 52, 29, 74], [13, 41, 67, 31]])
    print("center=", grid.rectangle_sum(0, 1, 2, 3), sep="")
    print("full=", grid.rectangle_sum(0, 0, 3, 4), sep="")
    print("empty=", grid.rectangle_sum(1, 2, 1, 4), sep="")
