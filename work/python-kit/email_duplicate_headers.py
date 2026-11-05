from email import policy
from email.parser import BytesParser

parser = BytesParser(policy=policy.default)
repeated = parser.parsebytes(
    b"From: receipts@aitrove.in\r\nFrom: audit@aitrove.in\r\n"
    b"Subject: R-47\r\n\r\npaid\r\n"
)
single = parser.parsebytes(
    b"From: receipts@aitrove.in\r\nSubject: R-73\r\n\r\npaid\r\n"
)
print("repeated_count", len(repeated.get_all("From", [])))
print("repeated_rejected", len(repeated.get_all("From", [])) != 1)
print("single_accepted", len(single.get_all("From", [])) == 1)
