def progress_counter():
    completed = 0
    def record_completion():
        nonlocal completed
        completed += 1
        return completed
    return record_completion

record = progress_counter()
labels = [lambda receipt_id=receipt_id: receipt_id for receipt_id in (41, 42)]
print(record(), record())
print([label() for label in labels])
