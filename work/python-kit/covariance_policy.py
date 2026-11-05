import math

def paired_covariance(left, right, *, sample=True):
    if type(sample) is not bool or type(left) is not list or type(right) is not list or not 2 <= len(left) == len(right) <= 64:
        raise ValueError("paired lengths")
    if any(type(value) not in (int, float) or abs(value) > 1000000 or not math.isfinite(value) for value in left + right):
        raise ValueError("finite bounded observations")
    count = len(left)
    left_mean, right_mean = math.fsum(left) / count, math.fsum(right) / count
    centered = math.fsum((x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True))
    return centered / (count - int(sample))

print("sample:", paired_covariance([1, 2, 3], [2, 4, 10]))
print("population:", round(paired_covariance([1, 2, 3], [2, 4, 10], sample=False), 6))
try:
    paired_covariance([1, 2], [2, float("nan")])
except ValueError:
    print("nonfinite pair rejected")
