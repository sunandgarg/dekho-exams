def label_distance(stored, imported):
    if not isinstance(stored, str) or not isinstance(imported, str):
        raise ValueError("text labels required")
    if max(len(stored), len(imported)) > 64:
        raise ValueError("label budget exceeded")
    if len(imported) > len(stored):
        stored, imported = imported, stored
    previous = list(range(len(imported) + 1))
    for row, stored_char in enumerate(stored, 1):
        current = [row]
        for column, imported_char in enumerate(imported, 1):
            current.append(min(current[-1] + 1, previous[column] + 1,
                               previous[column - 1] + (stored_char != imported_char)))
        previous = current
    return previous[-1]

print(label_distance("dispatch", "despatch"))
print(label_distance("", "DEL"))
try:
    label_distance("x" * 65, "DEL")
except ValueError:
    print("label budget rejected")
