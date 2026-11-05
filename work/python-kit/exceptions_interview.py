def accepted_import():
    try:
        raise OSError("owned fixture input unavailable")
    except OSError as cause:
        raise ValueError("receipt import rejected") from cause

def incorrect_finally_return():
    try:
        raise ValueError("receipt rejected")
    finally:
        return "incorrect success"

try:
    accepted_import()
except ValueError as failure:
    print("visible:", type(failure).__name__)
    print("cause:", type(failure.__cause__).__name__)
print("suppressed failure:", incorrect_finally_return())
