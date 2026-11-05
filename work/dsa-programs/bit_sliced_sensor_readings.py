class ReadingBitSlices:
    def __init__(self, readings, width=8):
        if width < 1 or any(not isinstance(reading, int) or not 0 <= reading < 1 << width
                            for reading in readings):
            raise ValueError("readings must fit the unsigned fixed-width domain")
        self.readings = list(readings)
        self.width = width
        self.slices = [0] * width
        for row, reading in enumerate(readings):
            for bit in range(width):
                if reading & (1 << bit):
                    self.slices[bit] |= 1 << row

    @property
    def all_rows(self):
        return (1 << len(self.readings)) - 1

    def replace(self, row, reading):
        if not 0 <= reading < 1 << self.width:
            raise ValueError("reading does not fit the column width")
        if not 0 <= row < len(self.readings):
            raise IndexError("row outside column")
        flag = 1 << row
        for bit in range(self.width):
            if reading & (1 << bit):
                self.slices[bit] |= flag
            else:
                self.slices[bit] &= ~flag
        self.readings[row] = reading

    def less_than(self, threshold):
        if threshold <= 0:
            return 0
        if threshold >= 1 << self.width:
            return self.all_rows
        equal, lower = self.all_rows, 0
        for bit in range(self.width - 1, -1, -1):
            ones = self.slices[bit]
            if threshold & (1 << bit):
                lower |= equal & ~ones
                equal &= ones
            else:
                equal &= ~ones
        return lower & self.all_rows

    def between(self, lower, upper):
        return self.less_than(upper + 1) & ~self.less_than(lower) & self.all_rows

    def sum_selected(self, row_mask):
        if row_mask & ~self.all_rows:
            raise ValueError("mask contains an unknown row")
        return sum((self.slices[bit] & row_mask).bit_count() << bit
                   for bit in range(self.width))


if __name__ == "__main__":
    index = ReadingBitSlices([47, 19, 83, 29, 61, 47])
    selected = index.between(29, 61)
    print([row for row in range(6) if selected & (1 << row)], index.sum_selected(selected))
    index.replace(2, 37)
    selected = index.between(29, 61)
    print([row for row in range(6) if selected & (1 << row)], index.sum_selected(selected))
