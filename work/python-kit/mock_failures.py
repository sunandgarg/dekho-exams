from unittest.mock import Mock

class ReceiptWriter:
    def publish(self, receipt):
        raise NotImplementedError

def import_receipt(receipt, writer, accepted):
    staged = dict(receipt)
    writer.publish(staged)
    accepted.append(staged["receipt_id"])

writer = Mock(spec_set=ReceiptWriter)
writer.publish.side_effect = OSError("fixture writer unavailable")
accepted = []
try:
    import_receipt({"receipt_id": "R-0041", "amount": 125}, writer, accepted)
except OSError:
    print("writer failure propagated")
writer.publish.assert_called_once_with({"receipt_id": "R-0041", "amount": 125})
print("accepted:", accepted)
