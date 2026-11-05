import hashlib
import math


class ScalableIncidentFilter:
    def __init__(self, first_capacity=4, error_budget=0.04):
        if first_capacity < 1 or not 0 < error_budget < 1:
            raise ValueError("invalid capacity or error budget")
        self.first_capacity = first_capacity
        self.error_budget = error_budget
        self.layers = []
        self._new_layer()

    def _new_layer(self):
        layer_number = len(self.layers)
        capacity = self.first_capacity * (2 ** layer_number)
        layer_budget = self.error_budget / (2 ** (layer_number + 1))
        bit_count = math.ceil(-capacity * math.log(layer_budget) / math.log(2) ** 2)
        hash_count = max(1, round(bit_count / capacity * math.log(2)))
        self.layers.append({"bits": bytearray(bit_count), "capacity": capacity,
                            "insertions": 0, "hash_count": hash_count})

    def _positions(self, incident_id, layer_number):
        layer = self.layers[layer_number]
        encoded = incident_id.encode("utf-8")
        for hash_number in range(layer["hash_count"]):
            digest = hashlib.blake2b(
                encoded + layer_number.to_bytes(4, "big")
                + hash_number.to_bytes(4, "big"), digest_size=8
            ).digest()
            yield int.from_bytes(digest, "big") % len(layer["bits"])

    def add(self, incident_id):
        if self.layers[-1]["insertions"] == self.layers[-1]["capacity"]:
            self._new_layer()
        layer_number = len(self.layers) - 1
        layer = self.layers[-1]
        for position in self._positions(incident_id, layer_number):
            layer["bits"][position] = 1
        layer["insertions"] += 1

    def might_contain(self, incident_id):
        return any(all(self.layers[layer_number]["bits"][position]
                       for position in self._positions(incident_id, layer_number))
                   for layer_number in range(len(self.layers)))


filter_index = ScalableIncidentFilter(first_capacity=4)
for incident_number in range(47, 62):
    filter_index.add(f"incident-{incident_number}")
print("layers=", len(filter_index.layers),
      "first=", filter_index.might_contain("incident-47"),
      "last=", filter_index.might_contain("incident-61"), sep="")
