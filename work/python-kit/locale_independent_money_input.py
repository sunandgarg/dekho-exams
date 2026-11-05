from decimal import Decimal

ASCII_DIGITS = set("0123456789")

def parse_payment_amount(raw_amount):
    whole, separator, cents = raw_amount.partition(".")
    if (separator != "." or not whole or len(cents) != 2
            or (len(whole) > 1 and whole.startswith("0"))
            or any(character not in ASCII_DIGITS for character in whole + cents)):
        raise ValueError("amount must use canonical decimal format")
    return Decimal(raw_amount)

print("accepted", parse_payment_amount("47.25"))
try:
    parse_payment_amount("47,25")
except ValueError:
    print("comma_rejected", True)
