def align_labels(source, target):
    if not isinstance(source, str) or not isinstance(target, str) or max(len(source), len(target)) > 32:
        raise ValueError("bounded labels required")
    costs = [[0] * (len(target) + 1) for _ in range(len(source) + 1)]
    for row in range(len(source) + 1): costs[row][0] = row
    for column in range(len(target) + 1): costs[0][column] = column
    for row in range(1, len(source) + 1):
        for column in range(1, len(target) + 1):
            costs[row][column] = min(costs[row - 1][column] + 1, costs[row][column - 1] + 1,
                                     costs[row - 1][column - 1] + (source[row - 1] != target[column - 1]))
    row, column = len(source), len(target); reversed_steps = []
    while row or column:
        if row and column and costs[row][column] == costs[row - 1][column - 1] + (source[row - 1] != target[column - 1]):
            kind = "keep" if source[row - 1] == target[column - 1] else "replace"
            reversed_steps.append((kind, source[row - 1], target[column - 1])); row -= 1; column -= 1
        elif row and costs[row][column] == costs[row - 1][column] + 1:
            reversed_steps.append(("delete", source[row - 1], "")); row -= 1
        else:
            reversed_steps.append(("insert", "", target[column - 1])); column -= 1
    return costs[-1][-1], list(reversed(reversed_steps))

def apply_alignment(source, steps):
    position = 0; output = []
    for kind, before, after in steps:
        if kind not in {"keep", "replace", "delete", "insert"}:
            raise ValueError("unknown alignment operation")
        if kind != "insert":
            if position >= len(source) or source[position] != before:
                raise ValueError("alignment source mismatch")
            position += 1
        if kind != "delete": output.append(after)
    if position != len(source):
        raise ValueError("alignment left source unconsumed")
    return "".join(output)

distance, steps = align_labels("DEL", "DILHI")
print("distance:", distance)
print("reconstructed:", apply_alignment("DEL", steps))
print("edited steps:", sum(kind != "keep" for kind, before, after in steps))
