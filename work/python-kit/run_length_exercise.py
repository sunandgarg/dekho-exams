def encode_states(states):
    if type(states) is not str or len(states) > 100 or not states.isascii() or not states.isalpha():
        if states != "":
            raise ValueError("ASCII status sequence")
    if not states:
        return []
    encoded = []
    current, count = states[0], 1
    for state in states[1:]:
        if state == current:
            count += 1
        else:
            encoded.append((current, count))
            current, count = state, 1
    encoded.append((current, count))
    return encoded

print(encode_states("QQSQQ"))
print(encode_states(""))
try:
    encode_states("Q１")
except ValueError:
    print("non-ASCII state rejected")
