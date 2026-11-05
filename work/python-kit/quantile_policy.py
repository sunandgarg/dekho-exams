import math
import statistics

def quartiles(durations, method):
    if type(durations) is not list or not 2 <= len(durations) <= 128 or method not in ("inclusive", "exclusive") or any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1000000 for value in durations):
        raise ValueError("bounded finite durations and declared policy required")
    return statistics.quantiles(durations, n=4, method=method)

durations = [100, 200, 300, 400]
print("inclusive:", quartiles(durations, "inclusive"))
print("exclusive:", quartiles(durations, "exclusive"))
try:
    quartiles([100, float("nan")], "inclusive")
except ValueError:
    print("nonfinite duration rejected")
