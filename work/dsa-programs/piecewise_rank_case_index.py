from bisect import bisect_left


class PiecewiseCaseRank:
    def __init__(self, sorted_case_ids, block_width=4):
        if block_width < 2 or any(left >= right for left, right in zip(sorted_case_ids, sorted_case_ids[1:])):
            raise ValueError("need strictly increasing IDs and block width at least two")
        self.keys = list(sorted_case_ids)
        self.blocks = []
        for start in range(0, len(self.keys), block_width):
            values = self.keys[start:start + block_width]
            first, last = values[0], values[-1]

            def predict(target):
                return 0 if first == last else (target - first) * (len(values) - 1) // (last - first)

            max_error = max(abs(predict(key) - offset) for offset, key in enumerate(values))
            self.blocks.append((first, last, start, len(values), max_error))
        self.ends = [block[1] for block in self.blocks]

    def lower_bound(self, target):
        if not self.blocks:
            return 0
        block_id = bisect_left(self.ends, target)
        if block_id == len(self.blocks):
            return len(self.keys)
        first, last, start, count, error = self.blocks[block_id]
        local_prediction = (0 if first == last or target <= first else
                            (target - first) * (count - 1) // (last - first))
        prediction = start + local_prediction
        low = max(start, prediction - error - 2)
        high = min(start + count, prediction + error + 3)
        return low + bisect_left(self.keys, target, low, high) - low


if __name__ == "__main__":
    catalog = PiecewiseCaseRank([19, 29, 47, 61, 83, 103, 127, 149, 173], block_width=4)
    print("rank for 60:", catalog.lower_bound(60))
    print("rank for 103:", catalog.lower_bound(103))
    print("rank for 200:", catalog.lower_bound(200))
