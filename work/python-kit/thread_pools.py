from concurrent.futures import ThreadPoolExecutor

def checked_amount(amount):
    if amount <= 0:
        raise ValueError("positive amount required")
    return amount * 2

accepted = []
rejected = 0
with ThreadPoolExecutor(max_workers=2) as workers:
    futures = [workers.submit(checked_amount, amount) for amount in [125, 75, -1]]
    for future in futures:
        try:
            accepted.append(future.result())
        except ValueError:
            rejected += 1
print(sorted(accepted))
print("rejected:", rejected)
