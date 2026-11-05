class AlertUniverse:
    def __init__(self, universe):
        if universe < 2 or universe & (universe - 1):
            raise ValueError("universe must be a power of two")
        self.universe = universe
        self.minimum = self.maximum = None
        self.summary = None
        self.clusters = {}
        lower_bits = (universe.bit_length() - 1 + 1) // 2
        self.lower_size = 1 << lower_bits
        self.upper_size = universe // self.lower_size

    def _parts(self, key):
        return divmod(key, self.lower_size)

    def _key(self, high, low):
        return high * self.lower_size + low

    def contains(self, key):
        if not 0 <= key < self.universe:
            return False
        if key == self.minimum or key == self.maximum:
            return True
        if self.universe == 2 or self.minimum is None:
            return False
        high, low = self._parts(key)
        return high in self.clusters and self.clusters[high].contains(low)

    def insert(self, key):
        if not 0 <= key < self.universe:
            raise ValueError("alert ID outside universe")
        if self.contains(key):
            return False
        if self.minimum is None:
            self.minimum = self.maximum = key
            return True
        if key < self.minimum:
            key, self.minimum = self.minimum, key
        if self.universe > 2:
            high, low = self._parts(key)
            cluster = self.clusters.get(high)
            if cluster is None:
                cluster = self.clusters[high] = AlertUniverse(self.lower_size)
            if cluster.minimum is None:
                if self.summary is None:
                    self.summary = AlertUniverse(self.upper_size)
                self.summary.insert(high)
            cluster.insert(low)
        self.maximum = max(self.maximum, key)
        return True

    def remove(self, key):
        if not self.contains(key):
            return False
        if self.minimum == self.maximum:
            self.minimum = self.maximum = None
            return True
        if self.universe == 2:
            self.minimum = self.maximum = 1 - key
            return True
        if key == self.minimum:
            first_cluster = self.summary.minimum
            key = self._key(first_cluster, self.clusters[first_cluster].minimum)
            self.minimum = key
        high, low = self._parts(key)
        cluster = self.clusters[high]
        cluster.remove(low)
        if cluster.minimum is None:
            del self.clusters[high]
            self.summary.remove(high)
            if self.summary.minimum is None:
                self.summary = None
            if key == self.maximum:
                if self.summary is None:
                    self.maximum = self.minimum
                else:
                    last_cluster = self.summary.maximum
                    self.maximum = self._key(last_cluster, self.clusters[last_cluster].maximum)
        elif key == self.maximum:
            self.maximum = self._key(high, cluster.maximum)
        return True

    def successor(self, key):
        if self.minimum is None or key >= self.maximum:
            return None
        if key < self.minimum:
            return self.minimum
        if self.universe == 2:
            return self.maximum
        high, low = self._parts(key)
        cluster = self.clusters.get(high)
        if cluster is not None and cluster.maximum > low:
            return self._key(high, cluster.successor(low))
        later = self.summary.successor(high) if self.summary else None
        return None if later is None else self._key(later, self.clusters[later].minimum)


alerts = AlertUniverse(256)
for alert_id in [83, 19, 61, 47, 103, 29]:
    alerts.insert(alert_id)
print(alerts.successor(47), alerts.successor(83))
alerts.remove(61)
print(alerts.successor(47), alerts.minimum, alerts.maximum)
