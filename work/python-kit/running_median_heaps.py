from fractions import Fraction
from heapq import heappush, heappop

def running_medians(values):
    if type(values) is not list or len(values) > 100 or any(type(value) is not int or abs(value) > 10000 for value in values):
        raise ValueError("bounded samples")
    lower, upper, result = [], [], []
    for value in values:
        if not lower or value <= -lower[0]:
            heappush(lower, -value)
        else:
            heappush(upper, value)
        if len(lower) > len(upper) + 1:
            heappush(upper, -heappop(lower))
        elif len(upper) > len(lower):
            heappush(lower, -heappop(upper))
        result.append(Fraction(-lower[0]) if len(lower) > len(upper)
                      else Fraction(-lower[0] + upper[0], 2))
    return result

print([str(value) for value in running_medians([7, 2, 9, 4])])
try:
    running_medians([True])
except ValueError:
    print("boolean rejected")
