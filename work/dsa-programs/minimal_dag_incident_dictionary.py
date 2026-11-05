class MinimalIncidentDictionary:
    def __init__(self, words):
        trie = {"terminal": False, "edges": {}}
        for word in set(words):
            node = trie
            for character in word:
                node = node["edges"].setdefault(character, {"terminal": False, "edges": {}})
            node["terminal"] = True
        self.states = []
        registry = {}

        def intern(node):
            edges = tuple((character, intern(child))
                          for character, child in sorted(node["edges"].items()))
            signature = node["terminal"], edges
            if signature not in registry:
                registry[signature] = len(self.states)
                self.states.append((node["terminal"], dict(edges)))
            return registry[signature]

        self.root = intern(trie)

    def contains(self, word):
        state = self.root
        for character in word:
            state = self.states[state][1].get(character)
            if state is None:
                return False
        return self.states[state][0]


if __name__ == "__main__":
    dictionary = MinimalIncidentDictionary(["dock47", "rack47", "dock83", "rack83"])
    print(dictionary.contains("rack47"), dictionary.contains("rack"))
    print(len(dictionary.states), dictionary.root)
