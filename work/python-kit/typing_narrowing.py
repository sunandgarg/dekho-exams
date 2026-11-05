from typing import TypeGuard

def accepted_amounts(value: object) -> TypeGuard[list[int]]:
    return isinstance(value, list) and len(value) <= 64 and all(type(amount) is int and 0 <= amount <= 1000000 for amount in value)

received = [125, 250]
print("accepted:", accepted_amounts(received))
owned = tuple(received) if accepted_amounts(received) else ()
alias = received
alias.append("rejected")
print("shared still accepted:", accepted_amounts(received))
print("owned total:", sum(owned))
print("boolean accepted:", accepted_amounts([True]))
