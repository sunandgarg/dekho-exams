"""Fixed-width unsigned integer multiset with maximum-XOR partner queries."""

from dataclasses import dataclass, field


@dataclass
class BitNode:
    count: int = 0
    children: dict[int, "BitNode"] = field(default_factory=dict)


class AssetFingerprintTrie:
    def __init__(self, bit_width: int):
        if bit_width < 1:
            raise ValueError("bit width must be positive")
        self.bit_width = bit_width
        self.root = BitNode()

    def _check(self, fingerprint: int) -> None:
        if not isinstance(fingerprint, int) or isinstance(fingerprint, bool) or not 0 <= fingerprint < 1 << self.bit_width:
            raise ValueError("fingerprint exceeds the unsigned width")

    def add(self, fingerprint: int) -> None:
        self._check(fingerprint)
        node = self.root
        node.count += 1
        for shift in range(self.bit_width - 1, -1, -1):
            bit = (fingerprint >> shift) & 1
            node = node.children.setdefault(bit, BitNode())
            node.count += 1

    def count(self, fingerprint: int) -> int:
        self._check(fingerprint)
        node = self.root
        for shift in range(self.bit_width - 1, -1, -1):
            node = node.children.get((fingerprint >> shift) & 1)
            if node is None:
                return 0
        return node.count

    def remove(self, fingerprint: int) -> None:
        if self.count(fingerprint) == 0:
            raise KeyError(fingerprint)
        node = self.root
        node.count -= 1
        for shift in range(self.bit_width - 1, -1, -1):
            bit = (fingerprint >> shift) & 1
            child = node.children[bit]
            child.count -= 1
            if child.count == 0:
                del node.children[bit]
                return
            node = child

    def best_xor_partner(self, fingerprint: int) -> tuple[int, int]:
        self._check(fingerprint)
        if self.root.count == 0:
            raise ValueError("no fingerprints stored")
        node = self.root
        partner = 0
        for shift in range(self.bit_width - 1, -1, -1):
            wanted = 1 - ((fingerprint >> shift) & 1)
            chosen = wanted if wanted in node.children else 1 - wanted
            partner |= chosen << shift
            node = node.children[chosen]
        return partner, fingerprint ^ partner


fingerprints = AssetFingerprintTrie(8)
for fingerprint in (19, 47, 61, 83, 47):
    fingerprints.add(fingerprint)
print(fingerprints.best_xor_partner(26))
fingerprints.remove(47)
print(fingerprints.count(47))
fingerprints.remove(47)
print(fingerprints.count(47))
