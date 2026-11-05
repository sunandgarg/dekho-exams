def marker_positions(text, marker):
    if type(text) is not str or type(marker) is not str or len(text) > 4096 or not 1 <= len(marker) <= 128:
        raise ValueError("text or marker budget")
    prefix = [0] * len(marker)
    matched = 0
    for position in range(1, len(marker)):
        while matched and marker[position] != marker[matched]:
            matched = prefix[matched - 1]
        if marker[position] == marker[matched]:
            matched += 1
        prefix[position] = matched
    found, matched = [], 0
    for position, character in enumerate(text):
        while matched and character != marker[matched]:
            matched = prefix[matched - 1]
        if character == marker[matched]:
            matched += 1
        if matched == len(marker):
            found.append(position - len(marker) + 1)
            matched = prefix[matched - 1]
    return found

print(marker_positions("R41|R41|R42", "R41"))
print(marker_positions("aaaa", "aa"))
