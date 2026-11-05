"""Failure-linked trie for simultaneous, overlapping alert-term matches."""

from collections import deque


class AlertNode:
    def __init__(self):
        self.edges = {}
        self.failure = 0
        self.matches = []


class AlertIndex:
    def __init__(self, alert_terms):
        self.terms = tuple(alert_terms)
        if not self.terms or any(not term for term in self.terms):
            raise ValueError("alert terms must be nonempty")
        if len(set(self.terms)) != len(self.terms):
            raise ValueError("duplicate alert term")
        self.nodes = [AlertNode()]
        for term_number, term in enumerate(self.terms):
            position = 0
            for character in term:
                if character not in self.nodes[position].edges:
                    self.nodes[position].edges[character] = len(self.nodes)
                    self.nodes.append(AlertNode())
                position = self.nodes[position].edges[character]
            self.nodes[position].matches.append(term_number)

        pending = deque(self.nodes[0].edges.values())
        while pending:
            position = pending.popleft()
            for character, child in self.nodes[position].edges.items():
                fallback = self.nodes[position].failure
                while fallback and character not in self.nodes[fallback].edges:
                    fallback = self.nodes[fallback].failure
                self.nodes[child].failure = self.nodes[fallback].edges.get(character, 0)
                self.nodes[child].matches.extend(self.nodes[self.nodes[child].failure].matches)
                pending.append(child)

    def scan(self, message):
        position = 0
        found = []
        for offset, character in enumerate(message):
            while position and character not in self.nodes[position].edges:
                position = self.nodes[position].failure
            position = self.nodes[position].edges.get(character, 0)
            for term_number in self.nodes[position].matches:
                term = self.terms[term_number]
                found.append((offset - len(term) + 1, term))
        return found


alerts = AlertIndex(("heat", "eat", "seal"))
print(alerts.scan("overheat seal heat"))
