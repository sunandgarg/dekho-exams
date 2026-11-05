from random import Random


class AlertNode:
    def __init__(self, alert_id, height):
        self.alert_id = alert_id
        self.forward = [None] * height
        self.span = [0] * height


class RankedAlertIndex:
    def __init__(self, seed=947, maximum_height=20):
        self.head = AlertNode(None, maximum_height)
        self.height = 1
        self.length = 0
        self.maximum_height = maximum_height
        self.random = Random(seed)

    def _height(self):
        height = 1
        while height < self.maximum_height and self.random.getrandbits(1):
            height += 1
        return height

    def _predecessors(self, alert_id):
        update = [None] * self.maximum_height
        ranks = [0] * self.maximum_height
        current = self.head
        for level in range(self.height - 1, -1, -1):
            ranks[level] = 0 if level == self.height - 1 else ranks[level + 1]
            while current.forward[level] is not None and current.forward[level].alert_id < alert_id:
                ranks[level] += current.span[level]
                current = current.forward[level]
            update[level] = current
        return update, ranks

    def add(self, alert_id):
        update, ranks = self._predecessors(alert_id)
        next_node = update[0].forward[0]
        if next_node is not None and next_node.alert_id == alert_id:
            return False
        node_height = self._height()
        if node_height > self.height:
            for level in range(self.height, node_height):
                ranks[level] = 0
                update[level] = self.head
                self.head.span[level] = self.length
            self.height = node_height
        new_node = AlertNode(alert_id, node_height)
        for level in range(node_height):
            predecessor = update[level]
            distance = ranks[0] - ranks[level]
            new_node.forward[level] = predecessor.forward[level]
            new_node.span[level] = predecessor.span[level] - distance
            predecessor.forward[level] = new_node
            predecessor.span[level] = distance + 1
        for level in range(node_height, self.height):
            update[level].span[level] += 1
        self.length += 1
        return True

    def discard(self, alert_id):
        update, _ = self._predecessors(alert_id)
        target = update[0].forward[0]
        if target is None or target.alert_id != alert_id:
            return False
        for level in range(self.height):
            predecessor = update[level]
            if predecessor.forward[level] is target:
                predecessor.span[level] += target.span[level] - 1
                predecessor.forward[level] = target.forward[level]
            else:
                predecessor.span[level] -= 1
        while self.height > 1 and self.head.forward[self.height - 1] is None:
            self.height -= 1
        self.length -= 1
        return True

    def rank(self, alert_id):
        """Count IDs strictly below alert_id."""
        _, ranks = self._predecessors(alert_id)
        return ranks[0]

    def select(self, position):
        if position < 0 or position >= self.length:
            raise IndexError(position)
        traversed = 0
        current = self.head
        for level in range(self.height - 1, -1, -1):
            while current.forward[level] is not None and traversed + current.span[level] <= position:
                traversed += current.span[level]
                current = current.forward[level]
        return current.forward[0].alert_id

    def ordered(self):
        result = []
        current = self.head.forward[0]
        while current is not None:
            result.append(current.alert_id)
            current = current.forward[0]
        return result


alert_index = RankedAlertIndex()
for alert_id in (61, 19, 83, 47, 29):
    alert_index.add(alert_id)
print("rank below 47:", alert_index.rank(47))
print("position two:", alert_index.select(2))
alert_index.discard(29)
print("after removal:", alert_index.ordered())
