from collections import defaultdict


class PositionalIncidentIndex:
    def __init__(self, documents):
        self.positions = defaultdict(lambda: defaultdict(list))
        for document_id, tokens in documents.items():
            for position, token in enumerate(tokens):
                self.positions[token][document_id].append(position)

    def phrase_documents(self, phrase):
        if not phrase:
            return []
        if any(token not in self.positions for token in phrase):
            return []
        candidates = set(self.positions[phrase[0]])
        for token in phrase[1:]:
            candidates.intersection_update(self.positions[token])
        found = []
        for document_id in sorted(candidates):
            positions = [set(self.positions[token][document_id]) for token in phrase]
            if any(all(start + offset in positions[offset] for offset in range(1, len(phrase)))
                   for start in positions[0]):
                found.append(document_id)
        return found


if __name__ == "__main__":
    incidents = PositionalIncidentIndex({
        103: ["pump", "pressure", "low", "pressure"],
        218: ["low", "pump", "pressure"],
        347: ["pump", "pressure", "pressure", "low"],
    })
    print("pump-pressure=", incidents.phrase_documents(["pump", "pressure"]), sep="")
    print("pressure-low=", incidents.phrase_documents(["pressure", "low"]), sep="")
    print("repeat=", incidents.phrase_documents(["pressure", "pressure"]), sep="")
