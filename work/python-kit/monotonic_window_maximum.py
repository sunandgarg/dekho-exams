from collections import deque

def window_peaks(samples, width):
    if type(samples) is not list or len(samples) > 100 or any(type(value) is not int for value in samples):
        raise ValueError("bounded integer samples")
    if type(width) is not int or not 1 <= width <= len(samples):
        raise ValueError("window width")
    candidates = deque()
    peaks = []
    for index, value in enumerate(samples):
        while candidates and candidates[0] <= index - width:
            candidates.popleft()
        while candidates and samples[candidates[-1]] <= value:
            candidates.pop()
        candidates.append(index)
        if index + 1 >= width:
            peaks.append(samples[candidates[0]])
    return peaks

print(window_peaks([4, 1, 3, 5, 2], 3))
try:
    window_peaks([4, 1], 0)
except ValueError:
    print("width rejected")
