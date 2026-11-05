import gc
import tracemalloc

tracemalloc.start()
try:
    baseline = tracemalloc.take_snapshot()
    retained = [bytearray(1024) for _ in range(64)]
    current, peak = tracemalloc.get_traced_memory()
    snapshot = tracemalloc.take_snapshot()
    positive_growth = sum(max(0, row.size_diff) for row in snapshot.compare_to(baseline, "lineno"))
    retained.clear()
    del retained, snapshot, baseline
    gc.collect()
    released, _ = tracemalloc.get_traced_memory()
    print("owned growth observed:", positive_growth >= 64 * 1024)
    print("release reduced current:", released < current // 2)
    print("peak includes retained:", peak >= current)
finally:
    tracemalloc.stop()
