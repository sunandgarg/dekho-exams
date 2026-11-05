from collections import Counter
from math import isqrt


def distinct_in_windows(scan_codes, windows):
    size = len(scan_codes)
    for start, stop in windows:
        if not 0 <= start <= stop <= size:
            raise IndexError("invalid half-open scan window")
    width = max(1, isqrt(size))
    ordered = sorted(enumerate(windows), key=lambda request: (request[1][0] // width, request[1][1]))
    counts = Counter()
    answers = [0] * len(windows)
    left = right = distinct = 0

    def add(position):
        nonlocal distinct
        code = scan_codes[position]
        if counts[code] == 0:
            distinct += 1
        counts[code] += 1

    def remove(position):
        nonlocal distinct
        code = scan_codes[position]
        counts[code] -= 1
        if counts[code] == 0:
            del counts[code]
            distinct -= 1

    for original, (start, stop) in ordered:
        while left > start:
            left -= 1
            add(left)
        while right < stop:
            add(right)
            right += 1
        while left < start:
            remove(left)
            left += 1
        while right > stop:
            right -= 1
            remove(right)
        answers[original] = distinct
    return answers


if __name__ == "__main__":
    codes = ["D47", "D19", "D47", "D61", "D19", "D83", "D47"]
    requests = [(1, 6), (0, 3), (3, 3), (2, 7)]
    print("distinct=", distinct_in_windows(codes, requests), sep="")
