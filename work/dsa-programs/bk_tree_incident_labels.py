def edit_distance(first_label, second_label):
    previous = list(range(len(second_label) + 1))
    for row, first_letter in enumerate(first_label, 1):
        current = [row]
        for column, second_letter in enumerate(second_label, 1):
            current.append(min(current[-1] + 1, previous[column] + 1,
                               previous[column - 1] + (first_letter != second_letter)))
        previous = current
    return previous[-1]


class IncidentLabelBKTree:
    def __init__(self):
        self.root = None

    def insert(self, label):
        if not label:
            raise ValueError("empty labels are not indexed")
        if self.root is None:
            self.root = {"label": label, "children": {}}
            return True
        node = self.root
        while True:
            distance = edit_distance(label, node["label"])
            if distance == 0:
                return False
            child = node["children"].get(distance)
            if child is None:
                node["children"][distance] = {"label": label, "children": {}}
                return True
            node = child

    def within(self, query, radius):
        if radius < 0:
            raise ValueError("radius must be nonnegative")
        if self.root is None:
            return []
        matches = []
        pending = [self.root]
        while pending:
            node = pending.pop()
            distance = edit_distance(query, node["label"])
            if distance <= radius:
                matches.append((distance, node["label"]))
            for edge, child in node["children"].items():
                if distance - radius <= edge <= distance + radius:
                    pending.append(child)
        return sorted(matches)


if __name__ == "__main__":
    labels = IncidentLabelBKTree()
    for label in ["invoice", "invoces", "invoices", "incident", "invoker", "voice"]:
        labels.insert(label)
    print("near invoice:", labels.within("invoice", 1))
    print("duplicate:", labels.insert("invoice"))
