class FrequencyBucket:
    def __init__(self, count):
        self.count = count
        self.keys = set()
        self.previous = None
        self.next = None


class AlertFrequencyIndex:
    def __init__(self):
        self.head = FrequencyBucket(0)
        self.tail = FrequencyBucket(0)
        self.head.next = self.tail
        self.tail.previous = self.head
        self.location = {}

    def _insert_after(self, anchor, count):
        bucket = FrequencyBucket(count)
        bucket.previous, bucket.next = anchor, anchor.next
        anchor.next.previous = bucket
        anchor.next = bucket
        return bucket

    def _remove_empty(self, bucket):
        if bucket.keys:
            return
        bucket.previous.next = bucket.next
        bucket.next.previous = bucket.previous

    def increment(self, alert_code):
        current = self.location.get(alert_code, self.head)
        target_count = current.count + 1
        target = current.next
        if target is self.tail or target.count != target_count:
            target = self._insert_after(current, target_count)
        target.keys.add(alert_code)
        self.location[alert_code] = target
        if current is not self.head:
            current.keys.remove(alert_code)
            self._remove_empty(current)

    def decrement(self, alert_code):
        current = self.location.get(alert_code)
        if current is None:
            raise KeyError(alert_code)
        if current.count == 1:
            del self.location[alert_code]
        else:
            target = current.previous
            if target is self.head or target.count != current.count - 1:
                target = self._insert_after(current.previous, current.count - 1)
            target.keys.add(alert_code)
            self.location[alert_code] = target
        current.keys.remove(alert_code)
        self._remove_empty(current)

    def minimum(self):
        return None if self.head.next is self.tail else next(iter(self.head.next.keys))

    def maximum(self):
        return None if self.tail.previous is self.head else next(iter(self.tail.previous.keys))


alerts = AlertFrequencyIndex()
for alert_code in ["dock-47", "dock-19", "dock-47", "dock-61", "dock-47", "dock-19"]:
    alerts.increment(alert_code)
print(alerts.minimum(), alerts.maximum())
alerts.decrement("dock-47")
alerts.decrement("dock-47")
print(alerts.minimum() in {"dock-47", "dock-61"}, alerts.maximum())
alerts.decrement("dock-61")
print(alerts.minimum(), alerts.maximum())
