CODECS = {}
class CodecMeta(type):
    def __new__(metaclass, name, bases, namespace, **options):
        wire_name = namespace.get("wire_name")
        if wire_name is not None:
            if not isinstance(wire_name, str) or not wire_name or wire_name in CODECS:
                raise ValueError("wire name rejected")
            if not callable(namespace.get("decode")):
                raise ValueError("decode function required")
        created = super().__new__(metaclass, name, bases, namespace, **options)
        if wire_name is not None:
            CODECS[wire_name] = created
        return created

class ReceiptCodec(metaclass=CodecMeta):
    wire_name = None

class ReceiptJson(ReceiptCodec):
    wire_name = "receipt-json"
    def decode(payload):
        return payload["receipt_id"]

print(CODECS["receipt-json"].decode({"receipt_id": "R-0041"}))
try:
    class DuplicateReceipt(ReceiptCodec):
        wire_name = "receipt-json"
        def decode(payload):
            return payload
except ValueError:
    print("duplicate class rejected")
print(CODECS["receipt-json"] is ReceiptJson)
