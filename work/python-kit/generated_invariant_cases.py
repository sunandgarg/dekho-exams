def parse_signed_decimal(raw):
    digits = raw[1:] if raw.startswith("-") else raw
    if not digits or not all("0" <= character <= "9" for character in digits):
        raise ValueError("not signed decimal")
    return int(raw)

checked = 0
for quantity in range(-47, 48):
    assert parse_signed_decimal(str(quantity)) == quantity
    checked += 1

rejected = 0
for raw in ("", "47x", " 47"):
    try:
        parse_signed_decimal(raw)
    except ValueError:
        rejected += 1
print("round_trips", checked)
print("rejected", rejected)
