from hypothesis import given, settings, strategies as st

def aggregate_quantities(quantities):
    if len(quantities) > 32:
        raise ValueError("batch budget rejected")
    total = 0
    for quantity in quantities:
        if type(quantity) is not int or not 0 <= quantity <= 20:
            raise ValueError("quantity rejected")
        total += quantity
    return total

@settings(max_examples=100, derandomize=True, database=None, deadline=None)
@given(st.lists(st.integers(min_value=0, max_value=20), max_size=32))
def accepted_property(quantities):
    assert aggregate_quantities(quantities) == sum(quantities)

@settings(max_examples=60, derandomize=True, database=None, deadline=None)
@given(st.one_of(st.booleans(), st.integers(max_value=-1), st.integers(min_value=21), st.text(max_size=8)))
def rejected_property(quantity):
    try:
        aggregate_quantities([quantity])
    except ValueError:
        return
    raise AssertionError("rejected field became accepted")

accepted_property()
rejected_property()
print("accepted and rejected properties passed")
