"""Ordered binary hash tree with index- and size-bound inclusion proofs."""

import hashlib


def leaf_digest(payload: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + payload).digest()


def branch_digest(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def committed_root(size: int, tree_digest: bytes) -> bytes:
    return hashlib.sha256(b"\x02" + size.to_bytes(8, "big") + tree_digest).digest()


class ScanBatchTree:
    def __init__(self, scan_records: list[bytes]):
        if not 0 < len(scan_records) < 1 << 64:
            raise ValueError("batch size must fit the root commitment")
        self.size = len(scan_records)
        self.levels = [[leaf_digest(record) for record in scan_records]]
        while len(self.levels[-1]) > 1:
            level = self.levels[-1]
            parents = [branch_digest(level[position], level[position + 1])
                       if position + 1 < len(level) else level[position]
                       for position in range(0, len(level), 2)]
            self.levels.append(parents)
        self.root = committed_root(self.size, self.levels[-1][0])

    def proof(self, position: int) -> list[tuple[str, bytes]]:
        if not 0 <= position < self.size:
            raise IndexError(position)
        siblings = []
        for level in self.levels[:-1]:
            peer = position ^ 1
            if peer < len(level):
                siblings.append(("left" if position & 1 else "right", level[peer]))
            position //= 2
        return siblings


def verify_scan(payload: bytes, position: int, size: int,
                proof: list[tuple[str, bytes]], trusted_root: bytes) -> bool:
    if not 0 <= position < size < 1 << 64 or not isinstance(trusted_root, bytes) or len(trusted_root) != 32:
        return False
    batch_size = size
    current = leaf_digest(payload)
    proof_position = 0
    while size > 1:
        peer = position ^ 1
        if peer < size:
            if proof_position >= len(proof):
                return False
            side, sibling = proof[proof_position]
            if side != ("left" if position & 1 else "right") or not isinstance(sibling, bytes) or len(sibling) != 32:
                return False
            current = branch_digest(sibling, current) if side == "left" else branch_digest(current, sibling)
            proof_position += 1
        position //= 2
        size = (size + 1) // 2
    return proof_position == len(proof) and committed_root(batch_size, current) == trusted_root


scans = [b"D-19:47", b"D-26:31", b"D-47:61", b"D-61:19", b"D-83:52"]
batch = ScanBatchTree(scans)
inclusion = batch.proof(3)
print(verify_scan(scans[3], 3, batch.size, inclusion, batch.root))
print(verify_scan(b"D-61:20", 3, batch.size, inclusion, batch.root))
print(len(inclusion))
