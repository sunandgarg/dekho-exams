late_callbacks = []
fixed_callbacks = []
for receipt_id in [41, 42, 43]:
    late_callbacks.append(lambda: receipt_id)
    fixed_callbacks.append(lambda captured=receipt_id: captured)
print([callback() for callback in late_callbacks])
print([callback() for callback in fixed_callbacks])
