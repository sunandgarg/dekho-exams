cleanup = []
def parsed_quantity(text):
    try:
        try:
            return int(text)
        except ValueError as cause:
            raise ValueError("quantity conversion rejected") from cause
    finally:
        cleanup.append("released")

print(parsed_quantity("3"))
try:
    parsed_quantity("invalid")
except ValueError as failure:
    print(str(failure))
    print("cause retained:", failure.__cause__ is not None)
print(cleanup)
