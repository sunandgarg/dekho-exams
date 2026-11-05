from dataclasses import dataclass, replace

@dataclass
class DispatchBatch:
    region: str
    receipt_ids: list[str]

original = DispatchBatch("north", ["R41"])
shared = replace(original, region="east")
shared.receipt_ids.append("R42")
isolated = replace(original, region="west", receipt_ids=list(original.receipt_ids))
isolated.receipt_ids.append("R43")
print(original.receipt_ids)
print(isolated.receipt_ids)
print(shared.receipt_ids is original.receipt_ids)
