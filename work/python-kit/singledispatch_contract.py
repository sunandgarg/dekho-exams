from functools import singledispatch

@singledispatch
def encoded_amount(amount):
    raise ValueError("unsupported representation")

@encoded_amount.register(int)
def encode_integer(amount):
    if type(amount) is not int or not 0 <= amount <= 1000:
        raise ValueError("bounded exact integer")
    return f"minor:{amount}"

@encoded_amount.register(bool)
def reject_boolean(amount):
    raise ValueError("boolean amount")

@encoded_amount.register(str)
def encode_text(amount):
    if not 1 <= len(amount) <= 4 or any(character not in "0123456789" for character in amount):
        raise ValueError("ASCII amount")
    return encode_integer(int(amount))

print(encoded_amount(125))
print(encoded_amount("75"))
for invalid in (True, 1.5, "-1"):
    try:
        encoded_amount(invalid)
    except ValueError:
        print("representation rejected")
