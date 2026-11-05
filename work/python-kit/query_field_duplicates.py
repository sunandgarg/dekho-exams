from urllib.parse import parse_qsl, urlencode

def parse_receipt_query(query):
    pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True,
                      errors="strict", max_num_fields=2)
    if len(pairs) != 2 or {name for name, _ in pairs} != {"receipt", "amount"}:
        raise ValueError("wrong or repeated fields")
    fields = dict(pairs)
    if not fields["receipt"] or not fields["amount"].isascii() or not fields["amount"].isdecimal():
        raise ValueError("invalid field")
    return fields["receipt"], int(fields["amount"])

wire_query = urlencode([("receipt", "R/47"), ("amount", "73")])
print("wire", wire_query)
print("parsed", parse_receipt_query(wire_query))
for rejected_query in ("receipt=R-47&receipt=R-73", "receipt=&amount=73",
                       "receipt=R-47&amount=73&mode=paid"):
    try:
        parse_receipt_query(rejected_query)
    except ValueError:
        print("rejected", rejected_query.split("&")[0])
