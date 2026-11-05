import os

raw_filename = b"receipt-\xff"
decoded_filename = os.fsdecode(raw_filename)
print("roundtrip", os.fsencode(decoded_filename) == raw_filename)
print("has_surrogate", any(0xDC80 <= ord(character) <= 0xDCFF
                           for character in decoded_filename))
