from collections import defaultdict


class TrigramIncidentIndex:
    def __init__(self, documents):
        self.documents = dict(documents)
        self.candidates = defaultdict(set)
        for document_id, text in self.documents.items():
            for start in range(len(text) - 2):
                self.candidates[text[start:start + 3]].add(document_id)

    def containing(self, fragment):
        if len(fragment) < 3:
            candidates = set(self.documents)
        else:
            grams = {fragment[start:start + 3] for start in range(len(fragment) - 2)}
            postings = [self.candidates.get(gram, set()) for gram in grams]
            postings.sort(key=len)
            candidates = postings[0].copy()
            for posting in postings[1:]:
                candidates.intersection_update(posting)
        return sorted(document_id for document_id in candidates if fragment in self.documents[document_id])


if __name__ == "__main__":
    index = TrigramIncidentIndex({
        103: "pressure valve warning",
        218: "pump pressure warning",
        347: "valve sensor alert",
        492: "pressure pressure",
    })
    print("pressure=", index.containing("pressure"), sep="")
    print("valve=", index.containing("valve"), sep="")
    print("short=", index.containing("ps"), sep="")
