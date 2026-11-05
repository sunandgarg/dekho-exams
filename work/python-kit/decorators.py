from functools import wraps

def positive_identifier(operation):
    @wraps(operation)
    def checked(identifier):
        if type(identifier) is not int or identifier <= 0:
            raise ValueError("positive integer identifier required")
        return operation(identifier)
    return checked

@positive_identifier
def lookup_receipt(identifier):
    return f"receipt:{identifier}"

print(lookup_receipt(41))
print(lookup_receipt.__name__)
try:
    lookup_receipt(0)
except ValueError:
    print("identifier rejected")
