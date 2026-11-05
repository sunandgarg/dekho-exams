import random


class IncidentReservoir:
    def __init__(self, capacity, seed=None):
        if capacity < 0:
            raise ValueError("capacity cannot be negative")
        self.capacity = capacity
        self.seen = 0
        self.values = []
        self.random_source = random.Random(seed)

    def record(self, incident_id):
        self.seen += 1
        if len(self.values) < self.capacity:
            self.values.append(incident_id)
        elif self.capacity:
            slot = self.random_source.randrange(self.seen)
            if slot < self.capacity:
                self.values[slot] = incident_id

    def sample(self):
        return list(self.values)


sampler = IncidentReservoir(4, seed=47)
for incident_number in range(47, 67):
    sampler.record(f"incident-{incident_number}")
print("seen=", sampler.seen, "sample=", sampler.sample(), sep="")
