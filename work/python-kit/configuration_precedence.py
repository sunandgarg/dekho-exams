def resolve_settings(defaults, file_settings, overrides):
    allowed = {"region", "workers"}
    for source in (defaults, file_settings, overrides):
        if set(source) - allowed:
            raise ValueError("unknown setting")
    merged = {**defaults, **file_settings, **overrides}
    if set(merged) != allowed or merged["region"] not in {"DEL", "BOM"}:
        raise ValueError("incomplete settings")
    if type(merged["workers"]) is not int or not 1 <= merged["workers"] <= 8:
        raise ValueError("invalid workers")
    return merged

defaults = {"region": "DEL", "workers": 2}
print(resolve_settings(defaults, {"workers": 3}, {"region": "BOM"}))
print(defaults)
try:
    resolve_settings(defaults, {}, {"workers": None})
except ValueError:
    print("null override rejected")
