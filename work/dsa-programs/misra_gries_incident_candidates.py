class FrequentIncidentCandidates:
    def __init__(self, slots):
        if slots < 1:
            raise ValueError("slots must be positive")
        self.slots = slots
        self.counts = {}
        self.seen = 0

    def record(self, incident_code):
        self.seen += 1
        if incident_code in self.counts:
            self.counts[incident_code] += 1
        elif len(self.counts) < self.slots:
            self.counts[incident_code] = 1
        else:
            for resident in list(self.counts):
                self.counts[resident] -= 1
                if self.counts[resident] == 0:
                    del self.counts[resident]

    def candidates(self):
        return sorted(self.counts)


incident_stream = ["pump-47", "valve-19", "pump-47", "sensor-61",
                   "pump-47", "valve-19", "pump-47", "grid-83",
                   "pump-47", "sensor-61", "pump-47"]
summary = FrequentIncidentCandidates(2)
for incident_code in incident_stream:
    summary.record(incident_code)
print("seen=", summary.seen, "candidates=", summary.candidates(), sep="")
