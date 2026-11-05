import re

def compressed_routes(words):
    if len(words) > 128 or any(not isinstance(word, str) or re.fullmatch(r"[A-Z]{1,32}", word) is None for word in words):
        raise ValueError("bounded route words required")
    root = {"terminal": False, "children": {}}
    for word in words:
        node = root
        for symbol in word:
            node = node["children"].setdefault(symbol, {"terminal": False, "children": {}})
        node["terminal"] = True
    def compress(node):
        result = {"terminal": node["terminal"], "edges": {}}
        for symbol, child in node["children"].items():
            label = symbol
            while not child["terminal"] and len(child["children"]) == 1:
                symbol, child = next(iter(child["children"].items())); label += symbol
            result["edges"][label] = compress(child)
        return result
    return compress(root)

def contains_route(root, word):
    if not isinstance(word, str) or re.fullmatch(r"[A-Z]{1,32}", word) is None:
        raise ValueError("route word rejected")
    position = 0; node = root
    while position < len(word):
        for label, child in node["edges"].items():
            if word.startswith(label, position):
                position += len(label); node = child; break
        else:
            return False
    return node["terminal"]

routes = compressed_routes(["DEL", "DELHI", "BOM"])
print("root labels:", sorted(routes["edges"]))
for word in ("DEL", "DELHI", "DE", "BOM"):
    print(word, contains_route(routes, word))
