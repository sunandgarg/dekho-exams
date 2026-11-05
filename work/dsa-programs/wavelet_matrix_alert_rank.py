class AlertWaveletMatrix:
    def __init__(self, alert_levels):
        if any(level < 0 for level in alert_levels):
            raise ValueError("alert levels must be nonnegative")
        self.length = len(alert_levels)
        self.width = max((level.bit_length() for level in alert_levels), default=1)
        self.width = max(1, self.width)
        self.prefix_ones = []
        self.zero_counts = []
        ordered = list(alert_levels)
        for shift in range(self.width - 1, -1, -1):
            zero_group, one_group = [], []
            prefix = [0]
            for level in ordered:
                bit = (level >> shift) & 1
                prefix.append(prefix[-1] + bit)
                (one_group if bit else zero_group).append(level)
            self.prefix_ones.append(prefix)
            self.zero_counts.append(len(zero_group))
            ordered = zero_group + one_group

    def _bounds(self, left, right):
        if not 0 <= left <= right <= self.length:
            raise IndexError("invalid half-open window")

    def frequency(self, level, left, right):
        self._bounds(left, right)
        if level < 0 or level >= (1 << self.width):
            return 0
        for depth, shift in enumerate(range(self.width - 1, -1, -1)):
            prefix = self.prefix_ones[depth]
            if (level >> shift) & 1:
                left = self.zero_counts[depth] + prefix[left]
                right = self.zero_counts[depth] + prefix[right]
            else:
                left -= prefix[left]
                right -= prefix[right]
        return right - left

    def kth(self, left, right, rank):
        self._bounds(left, right)
        if not 0 <= rank < right - left:
            raise IndexError("rank outside window")
        answer = 0
        for depth, shift in enumerate(range(self.width - 1, -1, -1)):
            prefix = self.prefix_ones[depth]
            left_zeros = left - prefix[left]
            right_zeros = right - prefix[right]
            zeros = right_zeros - left_zeros
            if rank < zeros:
                left, right = left_zeros, right_zeros
            else:
                rank -= zeros
                answer |= 1 << shift
                left = self.zero_counts[depth] + prefix[left]
                right = self.zero_counts[depth] + prefix[right]
        return answer


if __name__ == "__main__":
    matrix = AlertWaveletMatrix([47, 19, 83, 47, 29, 61, 19])
    print("third in [1,6):", matrix.kth(1, 6, 2))
    print("47 count in [0,5):", matrix.frequency(47, 0, 5))
    print("19 count in [2,7):", matrix.frequency(19, 2, 7))
