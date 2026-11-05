def wire_amount(text):
    if not 1 <= len(text) <= 8 or any(character not in "0123456789" for character in text):
        raise ValueError("ASCII digit field required")
    amount = int(text)
    if amount == 0:
        raise ValueError("positive amount required")
    return amount

print(wire_amount("125"))
for text in ["+125", " 125", "0", "１２５"]:
    try:
        wire_amount(text)
    except ValueError:
        print("field rejected")
