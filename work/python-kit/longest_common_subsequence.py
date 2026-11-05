def common_event_length(first, second):
    if type(first) is not str or type(second) is not str or max(len(first), len(second)) > 128:
        raise ValueError("sequence budget")
    if len(first) < len(second):
        first, second = second, first
    previous = [0] * (len(second) + 1)
    for first_event in first:
        current = [0]
        for index, second_event in enumerate(second, 1):
            current.append(previous[index - 1] + 1 if first_event == second_event
                           else max(previous[index], current[-1]))
        previous = current
    return previous[-1]

print(common_event_length("PACK", "PARK"))
print(common_event_length("", "PACK"))
