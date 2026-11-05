class IncidentExpiryWheel:
    def __init__(self, slot_count=8):
        if slot_count < 1:
            raise ValueError("wheel must have a positive number of slots")
        self.slot_count = slot_count
        self.now = 0
        self.slots = [set() for _ in range(slot_count)]
        self.active = {}

    def schedule(self, incident_id, delay, payload):
        if delay < 1:
            raise ValueError("delay must be positive")
        if incident_id in self.active:
            old_slot = self.active[incident_id][2]
            self.slots[old_slot].remove(incident_id)
        due = self.now + delay
        slot = due % self.slot_count
        self.active[incident_id] = (due, payload, slot)
        self.slots[slot].add(incident_id)

    def cancel(self, incident_id):
        due, payload, slot = self.active.pop(incident_id)
        self.slots[slot].remove(incident_id)
        return payload

    def get(self, incident_id):
        return self.active[incident_id][1]

    def advance(self, target_tick):
        if target_tick < self.now:
            raise ValueError("time cannot move backward")
        expired = []
        while self.now < target_tick:
            self.now += 1
            slot = self.now % self.slot_count
            for incident_id in tuple(self.slots[slot]):
                due, payload, _ = self.active[incident_id]
                if due <= self.now:
                    self.slots[slot].remove(incident_id)
                    del self.active[incident_id]
                    expired.append((incident_id, payload))
        return expired


wheel = IncidentExpiryWheel(8)
wheel.schedule(47, 3, "old-review")
wheel.schedule(19, 11, "valve-review")
wheel.schedule(47, 5, "new-review")
print("tick-3=", wheel.advance(3), " tick-5=", wheel.advance(5),
      " tick-11=", wheel.advance(11), sep="")
