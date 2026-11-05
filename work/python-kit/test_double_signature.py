from unittest.mock import create_autospec

def submit_receipt(receipt_id, *, region):
    return f"{region}:{receipt_id}"

submission = create_autospec(submit_receipt, return_value="queued")
print(submission(41, region="DEL"))
submission.assert_called_once_with(41, region="DEL")
try:
    submission(41, "DEL")
except TypeError:
    print("positional region rejected")
print("real function:", submit_receipt(41, region="DEL"))
