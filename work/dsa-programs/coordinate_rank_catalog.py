from bisect import bisect_left


class CoordinateRankCatalog:
    def __init__(self, shipment_weights):
        self.keys = sorted(set(shipment_weights))
        self.rank_by_weight = {weight: rank for rank, weight in enumerate(self.keys)}

    def rank(self, weight):
        return self.rank_by_weight[weight]

    def weight(self, rank):
        return self.keys[rank]

    def lower_bound(self, weight):
        return bisect_left(self.keys, weight)


if __name__ == "__main__":
    catalog = CoordinateRankCatalog([4700, -35, 4700, 82000, 19])
    print("keys=", catalog.keys, sep="")
    print("rank-4700=", catalog.rank(4700), sep="")
    print("first-at-least-20=", catalog.lower_bound(20), sep="")
    print("weight-at-rank-3=", catalog.weight(3), sep="")
