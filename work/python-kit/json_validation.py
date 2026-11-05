import json

def unique_members(pairs):
    values = {}
    for key, value in pairs:
        if key in values:
            raise ValueError("duplicate member")
        values[key] = value
    return values

def receipt_amount(text):
    if len(text) > 1024:
        raise ValueError("document too long")
    values = json.loads(text, object_pairs_hook=unique_members)
    if not isinstance(values, dict) or set(values) != {"amount_minor"}:
        raise ValueError("receipt shape required")
    amount = values["amount_minor"]
    if type(amount) is not int or amount <= 0:
        raise ValueError("positive integer amount required")
    return amount

print(receipt_amount('{"amount_minor":125}'))
for payload in ['{"amount_minor":true}', '{"amount_minor":1,"amount_minor":2}']:
    try:
        receipt_amount(payload)
    except ValueError:
        print("document rejected")
