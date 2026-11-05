"""An in-memory model of memtable flushes, immutable runs, and tombstones."""

from bisect import bisect_left


class RunIndex:
    def __init__(self, flush_limit: int = 3):
        if flush_limit <= 0:
            raise ValueError("flush_limit must be positive")
        self.flush_limit = flush_limit
        self.memtable: dict[str, str | None] = {}
        self.runs: list[tuple[tuple[str, str | None], ...]] = []

    def put(self, asset_id: str, value: str) -> None:
        self.memtable[asset_id] = value
        self._flush_if_full()

    def delete(self, asset_id: str) -> None:
        self.memtable[asset_id] = None
        self._flush_if_full()

    def _flush_if_full(self) -> None:
        if len(self.memtable) >= self.flush_limit:
            self.runs.append(tuple(sorted(self.memtable.items())))
            self.memtable.clear()

    def get(self, asset_id: str) -> str | None:
        if asset_id in self.memtable:
            return self.memtable[asset_id]
        for run in reversed(self.runs):
            position = bisect_left(run, asset_id, key=lambda item: item[0])
            if position < len(run) and run[position][0] == asset_id:
                return run[position][1]
        return None

    def compact_all(self) -> None:
        latest: dict[str, str | None] = {}
        for run in self.runs:
            latest.update(run)
        # All older runs are consumed, so their deletion markers can be dropped.
        self.runs = [tuple(sorted((key, value) for key, value in latest.items() if value is not None))] if latest else []


assets = RunIndex(flush_limit=2)
assets.put("A-19", "west")
assets.put("A-47", "north")
assets.put("A-19", "east")
assets.delete("A-47")
print(assets.get("A-19"))
print(assets.get("A-47"))
print(len(assets.runs))
assets.compact_all()
print(assets.runs)
