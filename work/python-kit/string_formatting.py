receipt_id = 41
amount_minor = 1275
major, minor = divmod(amount_minor, 100)
print(f"R{receipt_id:04d} | INR {major}.{minor:02d}")
