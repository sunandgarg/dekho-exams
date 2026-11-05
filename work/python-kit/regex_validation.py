import re

RECEIPT_ID = re.compile(r"R-[0-9]{4}")
def valid_receipt_id(text):
    return len(text) == 6 and RECEIPT_ID.fullmatch(text) is not None

for identifier in ["R-0041", "xR-0041", "R-0041\n", "R-００４１"]:
    print(valid_receipt_id(identifier))
