from collections import defaultdict


class KmerRouteIndex:
    def __init__(self, kmers):
        kmers = set(kmers)
        if not kmers or len({len(kmer) for kmer in kmers}) != 1 or len(next(iter(kmers))) < 2:
            raise ValueError("need equal-length k-mers with k at least two")
        self.k = len(next(iter(kmers)))
        outgoing = defaultdict(list)
        incoming = defaultdict(list)
        for kmer in sorted(kmers):
            source, target = kmer[:-1], kmer[1:]
            outgoing[source].append(kmer)
            incoming[target].append(kmer)
        self.vertices = set(outgoing) | set(incoming)
        self.outgoing = dict(outgoing)
        self.incoming = dict(incoming)
        self.edges = kmers

    def unitigs(self):
        used = set()
        paths = []

        def extend(first):
            sequence = first
            used.add(first)
            vertex = first[1:]
            while len(self.incoming.get(vertex, [])) == 1 and len(self.outgoing.get(vertex, [])) == 1:
                successor = self.outgoing[vertex][0]
                if successor in used:
                    break
                sequence += successor[-1]
                used.add(successor)
                vertex = successor[1:]
            return sequence

        for vertex in sorted(self.vertices):
            if len(self.incoming.get(vertex, [])) == 1 and len(self.outgoing.get(vertex, [])) == 1:
                continue
            for edge in self.outgoing.get(vertex, []):
                if edge not in used:
                    paths.append(extend(edge))
        for edge in sorted(self.edges):
            if edge not in used:
                paths.append(extend(edge))
        return paths


if __name__ == "__main__":
    index = KmerRouteIndex(["ATG", "TGA", "GAC", "ACT", "CTG", "TGC", "GCA"])
    print(index.unitigs())
    print(len(index.edges), len(index.vertices))
