class PersistentAlertMap:
    def __init__(self, root=None):
        self.root = root

    @staticmethod
    def _hash(alert_id):
        if not isinstance(alert_id, int) or alert_id < 0:
            raise ValueError("alert ID must be a nonnegative integer")
        return alert_id & 255

    @classmethod
    def _assoc(cls, node, alert_id, state, digest, shift):
        if node is None:
            return ("leaf", alert_id, state, digest)
        kind = node[0]
        if kind == "leaf":
            if node[1] == alert_id:
                return ("leaf", alert_id, state, digest)
            if shift == 8:
                return ("collision", ((node[1], node[2]), (alert_id, state)))
            branch = cls._assoc(None, node[1], node[2], node[3], shift)
            return cls._assoc(("branch", 1 << ((node[3] >> shift) & 15), (branch,)),
                              alert_id, state, digest, shift)
        if kind == "collision":
            pairs = dict(node[1])
            pairs[alert_id] = state
            return ("collision", tuple(sorted(pairs.items())))
        bitmap, children = node[1], node[2]
        slot = (digest >> shift) & 15
        bit = 1 << slot
        index = (bitmap & (bit - 1)).bit_count()
        if bitmap & bit:
            updated = list(children)
            updated[index] = cls._assoc(children[index], alert_id, state, digest, shift + 4)
            return ("branch", bitmap, tuple(updated))
        updated = list(children)
        updated.insert(index, ("leaf", alert_id, state, digest))
        return ("branch", bitmap | bit, tuple(updated))

    def set(self, alert_id, state):
        digest = self._hash(alert_id)
        return PersistentAlertMap(self._assoc(self.root, alert_id, state, digest, 0))

    def get(self, alert_id):
        digest = self._hash(alert_id)
        node = self.root
        shift = 0
        while node is not None:
            kind = node[0]
            if kind == "leaf":
                if node[1] == alert_id:
                    return node[2]
                raise KeyError(alert_id)
            if kind == "collision":
                for stored_id, state in node[1]:
                    if stored_id == alert_id:
                        return state
                raise KeyError(alert_id)
            slot = (digest >> shift) & 15
            bit = 1 << slot
            if not node[1] & bit:
                raise KeyError(alert_id)
            index = (node[1] & (bit - 1)).bit_count()
            node = node[2][index]
            shift += 4
        raise KeyError(alert_id)


revision_zero = PersistentAlertMap()
revision_one = revision_zero.set(47, "open").set(303, "review")
revision_two = revision_one.set(47, "closed")
print("old=", revision_one.get(47), " new=", revision_two.get(47),
      " collision=", revision_two.get(303), sep="")
