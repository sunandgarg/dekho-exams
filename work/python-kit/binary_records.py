import struct

RECEIPT = struct.Struct("!BII")
def encode_receipt(receipt_id, amount):
    if any(type(value) is not int or not 0 <= value <= 0xFFFFFFFF
           for value in (receipt_id, amount)):
        raise ValueError("unsigned exact integers required")
    return RECEIPT.pack(1, receipt_id, amount)

def decode_receipt(payload):
    if type(payload) is not bytes or len(payload) != RECEIPT.size:
        raise ValueError("exact record bytes required")
    version, receipt_id, amount = RECEIPT.unpack(payload)
    if version != 1:
        raise ValueError("unsupported version")
    return receipt_id, amount

payload = encode_receipt(41, 125)
print("bytes:", payload.hex())
print("record:", decode_receipt(payload))
for invalid in (payload[:-1], payload + b"x", bytes([2]) + payload[1:]):
    try:
        decode_receipt(invalid)
    except ValueError:
        print("record rejected")
