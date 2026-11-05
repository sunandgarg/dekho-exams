import re

def parse_quantity(text):
    if not isinstance(text, str) or re.fullmatch(r"[0-9]{1,3}", text) is None:
        raise ValueError("quantity grammar rejected")
    quantity = int(text)
    if quantity > 200:
        raise ValueError("quantity budget exceeded")
    return quantity

print(parse_quantity("125"))
print("builtin accepts sign:", int(" +3 "))
print("float truncation:", int(-3.8))
for text in ("+3", " 3", "３", True, "201"):
    try:
        parse_quantity(text)
    except ValueError:
        print("rejected")
