from copy import replace
from dataclasses import dataclass

@dataclass(frozen=True)
class InvoiceRevision:
    invoice_id: str
    status: str
    line_ids: tuple[str, ...]

pending = InvoiceRevision("inv-47", "pending", ("line-47", "line-48"))
approved = replace(pending, status="approved")
print("old", pending.status)
print("new", approved.status)
print("shared_immutable_lines", pending.line_ids is approved.line_ids)
