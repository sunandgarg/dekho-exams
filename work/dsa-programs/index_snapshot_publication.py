from dataclasses import dataclass
from threading import Lock
from types import MappingProxyType


@dataclass(frozen=True)
class InventorySnapshot:
    version: int
    bay_owners: object
    repair_windows: object


class InventoryIndexStore:
    def __init__(self, bay_owners, repair_windows):
        self.lock = Lock()
        self.current = self._build(1, dict(bay_owners), dict(repair_windows))

    @staticmethod
    def _build(version, bay_owners, repair_windows):
        if not set(repair_windows) <= set(bay_owners):
            raise ValueError("window has no bay")
        if any(start >= end for start, end in repair_windows.values()):
            raise ValueError("invalid repair window")
        return InventorySnapshot(
            version,
            MappingProxyType(bay_owners),
            MappingProxyType(repair_windows),
        )

    def read(self):
        with self.lock:
            return self.current

    def publish(self, expected_version, added_bays, removed_bays, changed_windows):
        with self.lock:
            if self.current.version != expected_version:
                raise ValueError("stale inventory version")
            bay_owners = dict(self.current.bay_owners)
            repair_windows = dict(self.current.repair_windows)
            for bay_id in removed_bays:
                bay_owners.pop(bay_id, None)
                repair_windows.pop(bay_id, None)
            bay_owners.update(added_bays)
            repair_windows.update(changed_windows)
            replacement = self._build(expected_version + 1, bay_owners, repair_windows)
            self.current = replacement
            return replacement


store = InventoryIndexStore({47: "north", 52: "east"}, {47: (19, 26), 52: (31, 42)})
before = store.read()
after = store.publish(before.version, {61: "west"}, (47,), {61: (47, 58)})
print(before.version, sorted(before.bay_owners), before.repair_windows[47])
print(after.version, sorted(after.bay_owners), after.repair_windows[61])
