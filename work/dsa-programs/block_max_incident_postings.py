class BlockMaxIncidentScores:
    def __init__(self, document_terms, block_width=16):
        if block_width < 1:
            raise ValueError("block width must be positive")
        self.block_width = block_width
        self.documents = {}
        self.block_documents = {}
        self.block_maximum = {}
        for document_id, weights in document_terms.items():
            if document_id < 0 or any(weight < 0 for weight in weights.values()):
                raise ValueError("IDs and term weights must be nonnegative")
            self.documents[document_id] = dict(weights)
            block = document_id // block_width
            self.block_documents.setdefault(block, []).append(document_id)
            for term, weight in weights.items():
                key = (term, block)
                self.block_maximum[key] = max(self.block_maximum.get(key, 0), weight)

    def top_k(self, query_terms, count):
        if count < 1:
            raise ValueError("count must be positive")
        terms = set(query_terms)
        leaders = []
        skipped = 0
        for block in sorted(self.block_documents):
            upper_bound = sum(self.block_maximum.get((term, block), 0) for term in terms)
            if len(leaders) == count and upper_bound < leaders[-1][0]:
                skipped += 1
                continue
            for document_id in self.block_documents[block]:
                score = sum(self.documents[document_id].get(term, 0) for term in terms)
                if score:
                    leaders.append((score, document_id))
                    leaders.sort(key=lambda item: (-item[0], item[1]))
                    del leaders[count:]
        return leaders, skipped


if __name__ == "__main__":
    index = BlockMaxIncidentScores({
        19: {"breach": 8}, 21: {"breach": 7, "urgent": 3},
        47: {"breach": 1}, 61: {"urgent": 2}, 83: {"breach": 1, "urgent": 1},
    }, block_width=20)
    print("top two:", index.top_k(["breach", "urgent"], 2))
