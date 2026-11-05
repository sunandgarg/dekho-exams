"""Disjoint-set union with XOR parity for same/different asset constraints."""


class ParityGroups:
    def __init__(self, assets: list[str]):
        if len(assets) != len(set(assets)):
            raise ValueError("asset IDs must be unique")
        self.parent = {asset: asset for asset in assets}
        self.size = {asset: 1 for asset in assets}
        self.to_parent = {asset: 0 for asset in assets}

    def find(self, asset: str) -> tuple[str, int]:
        parent = self.parent[asset]
        if parent == asset:
            return asset, 0
        leader, parent_parity = self.find(parent)
        self.to_parent[asset] ^= parent_parity
        self.parent[asset] = leader
        return leader, self.to_parent[asset]

    def constrain(self, first: str, second: str, different: bool) -> bool:
        first_root, first_parity = self.find(first)
        second_root, second_parity = self.find(second)
        required = int(different)
        if first_root == second_root:
            return first_parity ^ second_parity == required
        if self.size[first_root] < self.size[second_root]:
            first_root, second_root = second_root, first_root
        self.parent[second_root] = first_root
        self.to_parent[second_root] = first_parity ^ second_parity ^ required
        self.size[first_root] += self.size[second_root]
        return True

    def relationship(self, first: str, second: str) -> str:
        first_root, first_parity = self.find(first)
        second_root, second_parity = self.find(second)
        if first_root != second_root:
            return "unknown"
        return "different" if first_parity ^ second_parity else "same"


groups = ParityGroups(["A-19", "A-47", "A-61", "A-83"])
print(groups.constrain("A-19", "A-47", True))
print(groups.constrain("A-47", "A-61", True))
print(groups.relationship("A-19", "A-61"))
print(groups.constrain("A-19", "A-61", True))
print(groups.relationship("A-19", "A-83"))
