from itertools import tee

source_reads = []
def receipt_stream():
    for identifier in ("R41", "R42", "R43"):
        source_reads.append(identifier)
        yield identifier

fast, slow = tee(receipt_stream())
print(next(fast), next(fast))
print("upstream:", source_reads)
print("slow:", next(slow))
print("fast rest:", list(fast))
print("slow rest:", list(slow))
