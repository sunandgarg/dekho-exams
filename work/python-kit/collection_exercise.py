def validated_ledger(rows):
    if len(rows) > 1000:
        raise ValueError("batch too large")
    staged = {}
    for identifier, amount in rows:
        if type(identifier) is not int or type(amount) is not int or identifier <= 0 or amount <= 0:
            raise ValueError("positive integer fields required")
        if identifier in staged:
            raise ValueError("repeated receipt")
        staged[identifier] = amount
    return staged

print(validated_ledger([(41, 125), (42, 75)]))
try:
    validated_ledger([(41, 125), (41, 75)])
except ValueError:
    print("repeated receipt rejected")
