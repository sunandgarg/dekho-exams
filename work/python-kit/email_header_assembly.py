from email import policy
from email.message import EmailMessage

message = EmailMessage(policy=policy.SMTP)
try:
    message["Subject"] = "Receipt R-47 paid\nBcc: hidden"
except ValueError:
    print("newline_rejected", True)
message["Subject"] = "Receipt R-47 paid"
message.set_content("Receipt R-47 was recorded.")
serialized = message.as_bytes()
print("one_subject", serialized.count(b"Subject:") == 1)
print("body_present", b"Receipt R-47 was recorded." in serialized)
