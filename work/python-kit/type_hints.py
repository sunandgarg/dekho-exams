def declared_identifier(identifier: int) -> int:
    return identifier

def checked_identifier(identifier: int) -> int:
    if type(identifier) is not int or identifier <= 0:
        raise ValueError("positive integer identifier required")
    return identifier

print(declared_identifier("receipt-41"))
print(checked_identifier(41))
try:
    checked_identifier("receipt-41")
except ValueError:
    print("runtime value rejected")
