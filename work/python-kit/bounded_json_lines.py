import io
import json
import re

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError("duplicate JSON key")
        result[key] = value
    return result

def read_receipt_lines(source):
    staged = []; received = 0
    while True:
        line = source.readline(65)
        if not line: return staged
        received += len(line)
        if len(line) > 64 or not line.endswith(b"\n") or received > 128 or len(staged) >= 4:
            raise ValueError("stream budget rejected")
        record = json.loads(line.decode("utf-8"), object_pairs_hook=unique_object)
        if not isinstance(record, dict) or set(record) != {"id", "amount"}:
            raise ValueError("record fields rejected")
        if not isinstance(record["id"], str) or re.fullmatch(r"R-[0-9]{4}", record["id"]) is None:
            raise ValueError("identifier rejected")
        if type(record["amount"]) is not int or not 0 <= record["amount"] <= 1000000:
            raise ValueError("amount rejected")
        staged.append(record)

source = io.BytesIO(b'{"id":"R-0041","amount":125}\n{"id":"R-0042","amount":75}\n')
print(read_receipt_lines(source))
print("caller stream open:", not source.closed)
try:
    read_receipt_lines(io.BytesIO(b'{"id":"R-0041","amount":125}\n{"id":"R-0042","amount":true}\n'))
except ValueError:
    print("later row rejected")
