"""Two-choice integer set with relocation, rollback, and bounded rebuild attempts."""

MASK = (1 << 64) - 1


def mixed_slot(asset_id: int, table_id: int, capacity: int, salt: int) -> int:
    mixed = (asset_id + salt + (table_id + 1) * 0x9E3779B97F4A7C15) & MASK
    mixed = ((mixed ^ (mixed >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    mixed = ((mixed ^ (mixed >> 27)) * 0x94D049BB133111EB) & MASK
    return (mixed ^ (mixed >> 31)) & (capacity - 1)


class AssetCuckooSet:
    def __init__(self, capacity: int = 8):
        if capacity < 2 or capacity & (capacity - 1):
            raise ValueError("capacity must be a power of two and at least two")
        self.capacity = capacity
        self.salt = 0
        self.tables: list[list[int | None]] = [[None] * capacity for _ in range(2)]
        self.size = 0

    @staticmethod
    def _check(asset_id: int) -> None:
        if not isinstance(asset_id, int) or isinstance(asset_id, bool) or not 0 <= asset_id <= MASK:
            raise ValueError("asset ID must be an unsigned 64-bit integer")

    def contains(self, asset_id: int) -> bool:
        self._check(asset_id)
        return any(self.tables[table_id][mixed_slot(asset_id, table_id, self.capacity, self.salt)] == asset_id
                   for table_id in range(2))

    @staticmethod
    def _place(tables: list[list[int | None]], asset_id: int, capacity: int, salt: int) -> bool:
        pending = asset_id
        replacements: list[tuple[int, int, int | None]] = []
        for displacement in range(2 * capacity):
            table_id = displacement & 1
            slot = mixed_slot(pending, table_id, capacity, salt)
            occupant = tables[table_id][slot]
            replacements.append((table_id, slot, occupant))
            tables[table_id][slot] = pending
            if occupant is None:
                return True
            pending = occupant
        for table_id, slot, occupant in reversed(replacements):
            tables[table_id][slot] = occupant
        return False

    def _rebuild_with(self, new_asset_id: int) -> None:
        assets = [asset_id for table in self.tables for asset_id in table if asset_id is not None]
        assets.append(new_asset_id)
        candidate_capacity = self.capacity
        for attempt in range(24):
            if attempt and attempt % 4 == 0 or len(assets) > candidate_capacity:
                candidate_capacity *= 2
            candidate_salt = self.salt + attempt + 1
            candidate_tables: list[list[int | None]] = [[None] * candidate_capacity for _ in range(2)]
            if all(self._place(candidate_tables, asset_id, candidate_capacity, candidate_salt) for asset_id in assets):
                self.capacity = candidate_capacity
                self.salt = candidate_salt
                self.tables = candidate_tables
                self.size = len(assets)
                return
        raise RuntimeError("could not rebuild table; old set remains intact")

    def insert(self, asset_id: int) -> bool:
        self._check(asset_id)
        if self.contains(asset_id):
            return False
        if self.size < self.capacity and self._place(self.tables, asset_id, self.capacity, self.salt):
            self.size += 1
        else:
            self._rebuild_with(asset_id)
        return True

    def remove(self, asset_id: int) -> bool:
        self._check(asset_id)
        for table_id in range(2):
            slot = mixed_slot(asset_id, table_id, self.capacity, self.salt)
            if self.tables[table_id][slot] == asset_id:
                self.tables[table_id][slot] = None
                self.size -= 1
                return True
        return False


assets = AssetCuckooSet()
for asset_id in (19, 47, 61, 83, 95):
    assets.insert(asset_id)
print(assets.contains(61), assets.contains(26))
print(assets.remove(47), assets.contains(47))
print(assets.size)
