def receipt_label(identifier):
    if identifier <= 0:
        raise ValueError("positive identifier required")
    return f"receipt:{identifier}"

if __name__ == "__main__":
    print(receipt_label(41))
