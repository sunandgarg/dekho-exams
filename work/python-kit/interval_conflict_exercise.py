def no_conflicts(reservations):
    if type(reservations) is not list or len(reservations) > 200:
        raise ValueError("reservation cap")
    for span in reservations:
        if type(span) is not tuple or len(span) != 2 or any(type(minute) is not int for minute in span) or not 0 <= span[0] < span[1] <= 1440:
            raise ValueError("half-open minute pair")
    ordered = sorted(reservations)
    return all(previous[1] <= current[0] for previous, current in zip(ordered, ordered[1:]))

print(no_conflicts([(60, 90), (0, 60)]))
print(no_conflicts([(60, 90), (89, 100)]))
print(no_conflicts([]))
try:
    no_conflicts([(True, 60)])
except ValueError:
    print("boolean minute rejected")
