from bisect import bisect_left


class ChunkedAlertBitmap:
    CHUNK_WIDTH = 256
    PROMOTE_AT = 32
    DEMOTE_AT = 16

    def __init__(self):
        self.containers = {}
        self.counts = {}

    @staticmethod
    def _parts(alert_id):
        if not 0 <= alert_id < 65536:
            raise ValueError("alert ID outside 16-bit domain")
        return alert_id >> 8, alert_id & 255

    def add(self, alert_id):
        high, low = self._parts(alert_id)
        container = self.containers.setdefault(high, [])
        if isinstance(container, list):
            position = bisect_left(container, low)
            if position < len(container) and container[position] == low:
                return
            container.insert(position, low)
            self.counts[high] = len(container)
            if len(container) > self.PROMOTE_AT:
                self.containers[high] = sum(1 << item for item in container)
        elif not (container >> low) & 1:
            self.containers[high] = container | (1 << low)
            self.counts[high] += 1

    def remove(self, alert_id):
        high, low = self._parts(alert_id)
        if high not in self.containers:
            raise KeyError(alert_id)
        container = self.containers[high]
        if isinstance(container, list):
            position = bisect_left(container, low)
            if position == len(container) or container[position] != low:
                raise KeyError(alert_id)
            container.pop(position)
            self.counts[high] = len(container)
        else:
            if not (container >> low) & 1:
                raise KeyError(alert_id)
            container &= ~(1 << low)
            self.counts[high] -= 1
            if self.counts[high] <= self.DEMOTE_AT:
                self.containers[high] = [item for item in range(self.CHUNK_WIDTH)
                                         if (container >> item) & 1]
            else:
                self.containers[high] = container
        if self.counts[high] == 0:
            del self.counts[high]
            del self.containers[high]

    def contains(self, alert_id):
        high, low = self._parts(alert_id)
        container = self.containers.get(high, [])
        if isinstance(container, list):
            position = bisect_left(container, low)
            return position < len(container) and container[position] == low
        return bool((container >> low) & 1)

    @staticmethod
    def _mask(container):
        return sum(1 << item for item in container) if isinstance(container, list) else container

    def intersection(self, other):
        matches = []
        for high in sorted(self.containers.keys() & other.containers.keys()):
            common = self._mask(self.containers[high]) & self._mask(other.containers[high])
            while common:
                lowest = common & -common
                matches.append((high << 8) | (lowest.bit_length() - 1))
                common ^= lowest
        return matches

    def values(self):
        values = []
        for high in sorted(self.containers):
            container = self.containers[high]
            if isinstance(container, list):
                values.extend((high << 8) | low for low in container)
            else:
                bits = container
                while bits:
                    lowest = bits & -bits
                    values.append((high << 8) | (lowest.bit_length() - 1))
                    bits ^= lowest
        return values


active = ChunkedAlertBitmap()
reviewed = ChunkedAlertBitmap()
for alert_id in [47, 61, 83, *range(512, 552)]:
    active.add(alert_id)
for alert_id in [47, 129, 515, 516, 517]:
    reviewed.add(alert_id)
print("shared=", active.intersection(reviewed),
      " dense-chunk=", isinstance(active.containers[2], int), sep="")
