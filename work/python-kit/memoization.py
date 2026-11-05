from functools import lru_cache

def minimum_packages(sizes, target):
    if type(target) is not int or not 0 <= target <= 100 or not 1 <= len(sizes) <= 20:
        raise ValueError("packing bounds")
    if any(type(size) is not int or size <= 0 for size in sizes):
        raise ValueError("positive package sizes required")
    unreachable = target + 1
    @lru_cache(maxsize=None)
    def solve(remaining):
        if remaining == 0:
            return 0
        return min((1 + solve(remaining - size) for size in sizes if size <= remaining), default=unreachable)
    answer = solve(target)
    return -1 if answer >= unreachable else answer

print(minimum_packages((3, 5), 11))
print(minimum_packages((4, 6), 7))
