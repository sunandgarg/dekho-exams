def distinct_span(sequence):
    if not isinstance(sequence, str) or not sequence.isascii() or len(sequence) > 256:
        raise ValueError("bounded ASCII sequence required")
    left = 0
    best = 0
    latest = {}
    for right, symbol in enumerate(sequence):
        left = max(left, latest.get(symbol, -1) + 1)
        latest[symbol] = right
        best = max(best, right - left + 1)
    return best

print(distinct_span("ABCADEAF"))
print(distinct_span(""))
try:
    distinct_span("DEL\u00e9")
except ValueError:
    print("wire alphabet rejected")
