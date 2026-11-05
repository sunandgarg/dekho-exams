class LinearCaseIndex:
    def __init__(self, bucket_capacity=3):
        if bucket_capacity < 1:
            raise ValueError("bucket capacity must be positive")
        self.bucket_capacity = bucket_capacity
        self.level = 0
        self.split = 0
        self.buckets = [set(), set()]
        self.size = 0

    def bucket_for(self, case_id):
        if case_id < 0:
            raise ValueError("case IDs must be nonnegative")
        base = 2 << self.level
        slot = case_id % base
        if slot < self.split:
            slot = case_id % (base * 2)
        return slot

    def contains(self, case_id):
        return case_id in self.buckets[self.bucket_for(case_id)]

    def insert(self, case_id):
        slot = self.bucket_for(case_id)
        if case_id in self.buckets[slot]:
            return False
        self.buckets[slot].add(case_id)
        self.size += 1
        if self.size > len(self.buckets) * self.bucket_capacity:
            self._split_next()
        return True

    def remove(self, case_id):
        slot = self.bucket_for(case_id)
        if case_id not in self.buckets[slot]:
            return False
        self.buckets[slot].remove(case_id)
        self.size -= 1
        return True

    def _split_next(self):
        base = 2 << self.level
        old_slot = self.split
        self.buckets.append(set())
        old_keys = self.buckets[old_slot]
        self.buckets[old_slot] = set()
        for case_id in old_keys:
            self.buckets[case_id % (base * 2)].add(case_id)
        self.split += 1
        if self.split == base:
            self.level += 1
            self.split = 0


if __name__ == "__main__":
    index = LinearCaseIndex(bucket_capacity=2)
    for case_id in [19, 29, 47, 61, 83, 103, 127]:
        index.insert(case_id)
    print("buckets:", len(index.buckets), "split:", index.split)
    print("has 61:", index.contains(61))
    print("removed 29:", index.remove(29))
    print("has 29:", index.contains(29))
