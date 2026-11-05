class SpaceSavingIncidents:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.entries = {}

    def record(self, incident_code):
        if incident_code in self.entries:
            estimate, error = self.entries[incident_code]
            self.entries[incident_code] = (estimate + 1, error)
        elif len(self.entries) < self.capacity:
            self.entries[incident_code] = (1, 0)
        else:
            victim = min(self.entries, key=lambda code: (self.entries[code][0], code))
            minimum = self.entries[victim][0]
            del self.entries[victim]
            self.entries[incident_code] = (minimum + 1, minimum)

    def candidates(self):
        return sorted(self.entries.items(), key=lambda pair: (-pair[1][0], pair[0]))


incident_stream = ["pump-47", "valve-19", "pump-47", "sensor-61",
                   "pump-47", "valve-19", "pump-47", "grid-83",
                   "pump-47", "sensor-61", "pump-47"]
summary = SpaceSavingIncidents(2)
for incident_code in incident_stream:
    summary.record(incident_code)
print("candidates=", summary.candidates(), sep="")
