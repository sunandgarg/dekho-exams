def pair_receipts(identifiers, amounts):
    if type(identifiers) is not list or type(amounts) is not list or len(identifiers) > 10 or len(amounts) > 10:
        raise ValueError("bounded feeds")
    return list(zip(identifiers, amounts, strict=True))

print(pair_receipts(["R41", "R42"], [125, 75]))
try:
    pair_receipts(["R41", "R42"], [125])
except ValueError:
    print("length mismatch rejected")
