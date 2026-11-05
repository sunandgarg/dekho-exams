import re

def valid_word(word):
    return isinstance(word, str) and re.fullmatch(r"[A-Z]{1,32}", word) is not None

def build_routes(words):
    if len(words) > 128 or any(not valid_word(word) for word in words):
        raise ValueError("route word budget rejected")
    root = {"terminal": False, "children": {}}
    for word in words:
        node = root
        for symbol in word:
            node = node["children"].setdefault(symbol, {"terminal": False, "children": {}})
        node["terminal"] = True
    return root

def remove_route(root, word):
    if not valid_word(word):
        raise ValueError("route word rejected")
    node = root; path = []
    for symbol in word:
        if symbol not in node["children"]:
            return False
        path.append((node, symbol)); node = node["children"][symbol]
    if not node["terminal"]:
        return False
    node["terminal"] = False
    for parent, symbol in reversed(path):
        child = parent["children"][symbol]
        if child["terminal"] or child["children"]:
            break
        del parent["children"][symbol]
    return True

def route_words(root):
    result = []
    def visit(node, prefix):
        if node["terminal"]:
            result.append(prefix)
        for symbol, child in sorted(node["children"].items()):
            visit(child, prefix + symbol)
    visit(root, "")
    return result

routes = build_routes(["DEL", "DELHI", "BOM"])
print(remove_route(routes, "DEL"), route_words(routes))
print(remove_route(routes, "DEL"), route_words(routes))
print(remove_route(routes, "DELHI"), route_words(routes))
