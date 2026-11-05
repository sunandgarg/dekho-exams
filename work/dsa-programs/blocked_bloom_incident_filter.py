import hashlib


class BlockedIncidentFilter:
    def __init__(self, block_count=16, bits_per_block=64, hash_count=4):
        if block_count < 1 or bits_per_block < 1 or hash_count < 1:
            raise ValueError("block, bit, and hash counts must be positive")
        self.blocks = [0] * block_count
        self.bits_per_block = bits_per_block
        self.hash_count = hash_count

    def _location(self, incident_id):
        encoded = incident_id.encode("utf-8")
        block_digest = hashlib.blake2b(encoded, digest_size=8).digest()
        block_number = int.from_bytes(block_digest, "big") % len(self.blocks)
        bit_numbers = []
        for hash_number in range(self.hash_count):
            digest = hashlib.blake2b(
                encoded + hash_number.to_bytes(4, "big"), digest_size=8
            ).digest()
            bit_numbers.append(int.from_bytes(digest, "big") % self.bits_per_block)
        return block_number, bit_numbers

    def add(self, incident_id):
        block_number, bit_numbers = self._location(incident_id)
        for bit_number in bit_numbers:
            self.blocks[block_number] |= 1 << bit_number

    def might_contain(self, incident_id):
        block_number, bit_numbers = self._location(incident_id)
        return all(self.blocks[block_number] & (1 << bit_number)
                   for bit_number in bit_numbers)


filter_index = BlockedIncidentFilter()
for incident_id in ("pump-47", "valve-19", "sensor-61"):
    filter_index.add(incident_id)
print("pump=", filter_index.might_contain("pump-47"),
      "blocks=", len(filter_index.blocks), sep="")
