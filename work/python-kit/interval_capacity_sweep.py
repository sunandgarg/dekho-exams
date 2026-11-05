reservations = [(9, 14), (14, 17), (12, 16)]
events = []
for start, end in reservations:
    if end <= start:
        raise ValueError("empty or reversed reservation")
    events.extend(((start, 1), (end, -1)))

active = 0
peak = 0
for _, change in sorted(events):
    active += change
    peak = max(peak, active)
print("peak docks:", peak)
