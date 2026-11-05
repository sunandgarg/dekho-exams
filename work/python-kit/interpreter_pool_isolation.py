from concurrent.futures import InterpreterPoolExecutor

reviewed_amounts = []

def score_receipt(amount):
    reviewed_amounts.append(amount)
    return amount * 2

if __name__ == "__main__":
    with InterpreterPoolExecutor(max_workers=2) as pool:
        scores = list(pool.map(score_receipt, (47, 48)))
    print("scores", scores)
    print("parent_reviews", len(reviewed_amounts))
