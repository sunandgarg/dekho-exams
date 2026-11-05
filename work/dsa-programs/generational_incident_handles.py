from dataclasses import dataclass


_EMPTY = object()


@dataclass(frozen=True)
class IncidentHandle:
    owner: object
    slot: int
    generation: int


class IncidentSlotStore:
    def __init__(self):
        self.owner = object()
        self.values = []
        self.generations = []
        self.free = []

    def insert(self, incident):
        if self.free:
            slot = self.free.pop()
            self.values[slot] = incident
        else:
            slot = len(self.values)
            self.values.append(incident)
            self.generations.append(0)
        return IncidentHandle(self.owner, slot, self.generations[slot])

    def get(self, handle):
        if (handle.owner is not self.owner or not 0 <= handle.slot < len(self.values)
                or handle.generation != self.generations[handle.slot]
                or self.values[handle.slot] is _EMPTY):
            raise KeyError("stale or foreign incident handle")
        return self.values[handle.slot]

    def remove(self, handle):
        incident = self.get(handle)
        self.values[handle.slot] = _EMPTY
        self.generations[handle.slot] += 1
        self.free.append(handle.slot)
        return incident


if __name__ == "__main__":
    store = IncidentSlotStore()
    old_handle = store.insert("pump-47")
    store.remove(old_handle)
    new_handle = store.insert("valve-19")
    print("same-slot=", old_handle.slot == new_handle.slot, sep="")
    print("new=", store.get(new_handle), sep="")
    try:
        store.get(old_handle)
    except KeyError:
        print("old=stale")
