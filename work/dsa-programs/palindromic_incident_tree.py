class PalindromicIncidentTree:
    def __init__(self):
        self.text = []
        self.nodes = [
            {"length": -1, "link": 0, "next": {}, "ends": 0},
            {"length": 0, "link": 0, "next": {}, "ends": 0},
        ]
        self.last = 1

    def _extendable(self, node_id, position, letter):
        length = self.nodes[node_id]["length"]
        return position - length - 1 >= 0 and self.text[position - length - 1] == letter

    def append(self, letter):
        if len(letter) != 1:
            raise ValueError("append exactly one code point")
        self.text.append(letter)
        position = len(self.text) - 1
        candidate = self.last
        while not self._extendable(candidate, position, letter):
            candidate = self.nodes[candidate]["link"]
        transition = self.nodes[candidate]["next"]
        if letter in transition:
            self.last = transition[letter]
            self.nodes[self.last]["ends"] += 1
            return False
        new_id = len(self.nodes)
        self.nodes.append({"length": self.nodes[candidate]["length"] + 2,
                           "link": 1, "next": {}, "ends": 1})
        transition[letter] = new_id
        if self.nodes[new_id]["length"] > 1:
            suffix = self.nodes[candidate]["link"]
            while not self._extendable(suffix, position, letter):
                suffix = self.nodes[suffix]["link"]
            self.nodes[new_id]["link"] = self.nodes[suffix]["next"][letter]
        self.last = new_id
        return True

    def distinct_count(self):
        return len(self.nodes) - 2

    def longest_length(self):
        return max((node["length"] for node in self.nodes[2:]), default=0)

    def occurrence_counts(self):
        counts = [node["ends"] for node in self.nodes]
        for node_id in sorted(range(2, len(self.nodes)),
                              key=lambda item: self.nodes[item]["length"], reverse=True):
            counts[self.nodes[node_id]["link"]] += counts[node_id]
        return {node_id: counts[node_id] for node_id in range(2, len(self.nodes))}


if __name__ == "__main__":
    index = PalindromicIncidentTree()
    for letter in "abacaba":
        index.append(letter)
    print("distinct:", index.distinct_count())
    print("longest:", index.longest_length())
    print("occurrences:", sorted(index.occurrence_counts().values()))
