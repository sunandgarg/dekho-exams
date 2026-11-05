import_state = ("tenant-a", [])
import_state[1].append("R41")
print(import_state)
receipt_key = ("tenant-a", 41)
print({receipt_key: 125}[receipt_key])
try:
    hash(import_state)
except TypeError:
    print("mutable component is unhashable")
