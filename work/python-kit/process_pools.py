from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

def receipt_checksum(receipt_id):
    if type(receipt_id) is not int or not 1 <= receipt_id <= 1000:
        raise ValueError("receipt ID out of range")
    return receipt_id * receipt_id % 97

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2, mp_context=get_context("spawn")) as pool:
        results = list(pool.map(receipt_checksum, [41, 42, 43]))
    print(results)
