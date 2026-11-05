defaults = {"window": 30, "depots": ["DEL"]}
configured = defaults | {"window": 15}
configured["depots"].append("BOM")
owned = configured | {"depots": list(configured["depots"])}
owned["depots"].append("MAA")
print(defaults)
print(configured["window"])
print(owned["depots"])
