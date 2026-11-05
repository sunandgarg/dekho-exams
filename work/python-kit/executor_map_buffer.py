from concurrent.futures import ThreadPoolExecutor

submitted = []

def receipt_ids():
    for number in range(47, 53):
        submitted.append(number)
        yield number

def normalize_receipt(number):
    return f"receipt-{number}"

with ThreadPoolExecutor(max_workers=2) as pool:
    results = pool.map(normalize_receipt, receipt_ids(), buffersize=2)
    print("pulled_before_next", len(submitted))
    print("first", next(results))
    print("all", len([*results]) + 1)
