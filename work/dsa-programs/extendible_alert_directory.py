class AlertBucket:
    def __init__(self, depth):
        self.depth = depth
        self.records = {}


class ExtendibleAlertDirectory:
    def __init__(self, bucket_capacity=2):
        if bucket_capacity < 1:
            raise ValueError("bucket capacity must be positive")
        self.bucket_capacity = bucket_capacity
        self.global_depth = 1
        self.directory = [AlertBucket(1), AlertBucket(1)]

    @staticmethod
    def _hash(alert_id):
        if not isinstance(alert_id, int) or alert_id < 0:
            raise ValueError("alert ID must be a nonnegative integer")
        return alert_id & 255

    def _index(self, alert_id):
        return self._hash(alert_id) & ((1 << self.global_depth) - 1)

    def get(self, alert_id):
        return self.directory[self._index(alert_id)].records[alert_id]

    def delete(self, alert_id):
        del self.directory[self._index(alert_id)].records[alert_id]

    def set(self, alert_id, state):
        index = self._index(alert_id)
        self.directory[index].records[alert_id] = state
        while len(self.directory[self._index(alert_id)].records) > self.bucket_capacity:
            bucket = self.directory[self._index(alert_id)]
            if bucket.depth == 8:
                break  # Identical eight-bit hashes remain in one collision bucket.
            old_depth = bucket.depth
            if old_depth == self.global_depth:
                self.directory += self.directory[:]
                self.global_depth += 1
            upper = AlertBucket(old_depth + 1)
            bucket.depth += 1
            for directory_index, candidate in enumerate(self.directory):
                if candidate is bucket and directory_index & (1 << old_depth):
                    self.directory[directory_index] = upper
            records = list(bucket.records.items())
            bucket.records.clear()
            for stored_id, stored_state in records:
                self.directory[self._index(stored_id)].records[stored_id] = stored_state


directory = ExtendibleAlertDirectory()
for alert_id in (47, 51, 55, 303):
    directory.set(alert_id, f"incident-{alert_id}")
print("depth=", directory.global_depth, " buckets=", len({id(bucket) for bucket in directory.directory}),
      " collision=", directory.get(303), sep="")
