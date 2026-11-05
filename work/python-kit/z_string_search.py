def z_matches(text, pattern):
    if type(text) is not str or type(pattern) is not str or len(text) > 128 or len(pattern) > 32:
        raise ValueError("bounded strings required")
    if not pattern:
        return list(range(len(text) + 1))
    symbols = list(pattern) + [object()] + list(text)
    matched = [0] * len(symbols)
    left = right = 0
    for position in range(1, len(symbols)):
        if position < right:
            matched[position] = min(right - position, matched[position - left])
        while position + matched[position] < len(symbols) and symbols[matched[position]] == symbols[position + matched[position]]:
            matched[position] += 1
        if position + matched[position] > right:
            left, right = position, position + matched[position]
    offset = len(pattern) + 1
    return [position - offset for position in range(offset, len(symbols)) if matched[position] >= len(pattern)]

print("overlaps:", z_matches("ababa", "aba"))
print("delimiter text:", z_matches("$a$a", "$a"))
print("empty:", z_matches("ab", ""))
