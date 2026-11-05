calls = 0
def charge(amount, /, *, fee=25):
    global calls
    if type(amount) is not int or amount < 0 or type(fee) is not int or fee < 0:
        raise ValueError("nonnegative exact integers required")
    calls += 1
    return amount + fee

print("charged:", charge(125, fee=50))
for arguments, keywords in (((), {"amount": 125}), ((125, 50), {})):
    try:
        charge(*arguments, **keywords)
    except TypeError:
        print("binding rejected")
print("body calls:", calls)
