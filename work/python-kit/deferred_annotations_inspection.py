from annotationlib import Format, get_annotations

def load_receipt(receipt_id: str) -> FutureReceipt:
    raise NotImplementedError

written = get_annotations(load_receipt, format=Format.STRING)
print("return_name", written["return"])
try:
    get_annotations(load_receipt, format=Format.VALUE)
except NameError:
    print("value_unresolved", True)
