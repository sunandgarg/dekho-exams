class EliasFanoAlertIds:
    def __init__(self, alert_ids, universe):
        if universe < 1 or any(not 0 <= alert_id < universe for alert_id in alert_ids):
            raise ValueError("alert ID outside universe")
        if any(left >= right for left, right in zip(alert_ids, alert_ids[1:])):
            raise ValueError("alert IDs must be strictly increasing")
        self.count = len(alert_ids)
        self.universe = universe
        ratio = max(1, universe // max(1, self.count))
        self.lower_width = ratio.bit_length() - 1
        mask = (1 << self.lower_width) - 1
        self.low_parts = [alert_id & mask for alert_id in alert_ids]
        high_capacity = ((universe - 1) >> self.lower_width) + self.count + 1
        self.high_bits = [0] * high_capacity
        self.one_positions = []
        for rank, alert_id in enumerate(alert_ids):
            position = (alert_id >> self.lower_width) + rank
            self.high_bits[position] = 1
            self.one_positions.append(position)

    def at(self, rank):
        if not 0 <= rank < self.count:
            raise IndexError("rank outside alert IDs")
        upper = self.one_positions[rank] - rank
        return (upper << self.lower_width) | self.low_parts[rank]

    def lower_bound(self, target):
        left, right = 0, self.count
        while left < right:
            middle = (left + right) // 2
            if self.at(middle) < target:
                left = middle + 1
            else:
                right = middle
        return self.at(left) if left < self.count else None

    def encoded_bit_count(self):
        return len(self.high_bits) + self.count * self.lower_width


alerts = EliasFanoAlertIds([13, 19, 47, 61, 83, 129], universe=256)
print("rank-3=", alerts.at(3), " next-50=", alerts.lower_bound(50),
      " conceptual-bits=", alerts.encoded_bit_count(), sep="")
