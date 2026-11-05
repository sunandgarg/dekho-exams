def package_cost(quantity: int, *, unit_minor: int) -> int:
    if type(quantity) is not int or type(unit_minor) is not int:
        raise TypeError("integer amounts required")
    if quantity < 0 or unit_minor < 0:
        raise ValueError("negative quantity or price")
    return quantity * unit_minor

print(package_cost(3, unit_minor=125))
try:
    package_cost(True, unit_minor=125)
except TypeError:
    print("boolean quantity rejected")
