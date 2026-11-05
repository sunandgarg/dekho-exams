def dispatch(*, region, priority=0):
    return f"{region}:{priority}"

print(dispatch(**{"region": "DEL"}, **{"priority": 2}))
try:
    dispatch(**{"region": "DEL"}, **{"region": "BOM"})
except TypeError:
    print("duplicate keyword rejected")
try:
    list(zip([41, 42], [125], strict=True))
except ValueError:
    print("incomplete record batch rejected")
