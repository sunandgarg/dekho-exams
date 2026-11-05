from typing import TypedDict

class AcceptedReceipt(TypedDict):
    receipt_id: str
    amount: int

def receipt_amount(amount: int) -> AcceptedReceipt:
    if type(amount) is not int or not 0 <= amount <= 1000000:
        raise ValueError("runtime amount rejected")
    return {"receipt_id": "R-0041", "amount": amount}

print(receipt_amount(125))
try: receipt_amount("125")
except ValueError: print("annotated call rejected by runtime check")
received: AcceptedReceipt = {"receipt_id": "R-0041", "amount": "unchecked"}
print("ordinary dictionary:", type(received) is dict)
print("annotation alone corrected value:", type(received["amount"]) is int)
