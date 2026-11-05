receipt_ids = ["R41", "R42"]
rejected_key = ("north", receipt_ids)
try:
    {rejected_key: 2}
except TypeError:
    print("mutable member rejected")
accepted_key = ("north", tuple(receipt_ids))
counts = {accepted_key: 2}
print(counts[("north", ("R41", "R42"))])
