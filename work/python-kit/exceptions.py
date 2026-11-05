def parse_minor_amount(text):
    try:
        amount = int(text)
    except ValueError as cause:
        raise ValueError("integer amount required") from cause
    if amount <= 0:
        raise ValueError("positive amount required")
    return amount

print(parse_minor_amount("125"))
try:
    parse_minor_amount("12x")
except ValueError as failure:
    print(str(failure))
    print(type(failure.__cause__).__name__)
