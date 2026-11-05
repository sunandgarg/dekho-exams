import ctypes

receipt_buffer = ctypes.create_string_buffer(b"R" * 47)
address = ctypes.addressof(receipt_buffer)
receipt_view = ctypes.memoryview_at(address, 47, readonly=True)
try:
    print("initial", bytes(receipt_view) == b"R" * 47)
    receipt_buffer[0] = b"S"
    print("owner_change_visible", bytes(receipt_view).startswith(b"S"))
finally:
    receipt_view.release()
