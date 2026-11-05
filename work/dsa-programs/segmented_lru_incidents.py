from collections import OrderedDict


class SegmentedIncidentCache:
    def __init__(self, probation_capacity=2, protected_capacity=2):
        if probation_capacity < 1 or protected_capacity < 1:
            raise ValueError("both segment capacities must be positive")
        self.probation_capacity = probation_capacity
        self.protected_capacity = protected_capacity
        self.probation = OrderedDict()
        self.protected = OrderedDict()

    def _trim_probation(self):
        if len(self.probation) > self.probation_capacity:
            return self.probation.popitem(last=False)[0]
        return None

    def get(self, incident_id):
        if incident_id in self.protected:
            self.protected.move_to_end(incident_id)
            return self.protected[incident_id]
        payload = self.probation.pop(incident_id)
        self.protected[incident_id] = payload
        if len(self.protected) > self.protected_capacity:
            demoted_id, demoted_payload = self.protected.popitem(last=False)
            self.probation[demoted_id] = demoted_payload
            self._trim_probation()
        return payload

    def put(self, incident_id, payload):
        if incident_id in self.protected:
            self.protected[incident_id] = payload
            self.protected.move_to_end(incident_id)
            return None
        if incident_id in self.probation:
            self.probation[incident_id] = payload
            self.probation.move_to_end(incident_id)
            return None
        self.probation[incident_id] = payload
        return self._trim_probation()


cache = SegmentedIncidentCache(2, 2)
for incident_id in (47, 19):
    cache.put(incident_id, f"incident-{incident_id}")
cache.get(47)
cache.put(61, "incident-61")
cache.get(61)
cache.get(19)
print("protected=", list(cache.protected), " probation=", list(cache.probation), sep="")
