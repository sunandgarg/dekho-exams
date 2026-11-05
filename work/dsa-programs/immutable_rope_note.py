class RopeNode:
    def __init__(self, text=None, left=None, right=None):
        self.text = text
        self.left = left
        self.right = right
        self.weight = left.length if left else 0
        self.length = len(text) if text is not None else self.weight + right.length


def join(left, right):
    if left is None:
        return right
    if right is None:
        return left
    return RopeNode(left=left, right=right)


def build_rope(text, chunk_size=5):
    if chunk_size < 1:
        raise ValueError("chunk size must be positive")
    nodes = [RopeNode(text=text[offset:offset + chunk_size])
             for offset in range(0, len(text), chunk_size)]
    while len(nodes) > 1:
        nodes = [join(nodes[index], nodes[index + 1])
                 if index + 1 < len(nodes) else nodes[index]
                 for index in range(0, len(nodes), 2)]
    return nodes[0] if nodes else None


def split(node, index):
    if node is None:
        if index != 0:
            raise IndexError("split outside note")
        return None, None
    if not 0 <= index <= node.length:
        raise IndexError("split outside note")
    if index == 0:
        return None, node
    if index == node.length:
        return node, None
    if node.text is not None:
        return build_rope(node.text[:index]), build_rope(node.text[index:])
    if index < node.weight:
        prefix, suffix = split(node.left, index)
        return prefix, join(suffix, node.right)
    prefix, suffix = split(node.right, index - node.weight)
    return join(node.left, prefix), suffix


def insert(node, index, text):
    left, right = split(node, index)
    return join(join(left, build_rope(text)), right)


def delete(node, start, end):
    if node is None or not 0 <= start <= end <= node.length:
        raise IndexError("delete outside note")
    left, remainder = split(node, start)
    _, right = split(remainder, end - start)
    return join(left, right)


def character_at(node, index):
    if node is None or not 0 <= index < node.length:
        raise IndexError("character outside note")
    while node.text is None:
        if index < node.weight:
            node = node.left
        else:
            index -= node.weight
            node = node.right
    return node.text[index]


def flatten(node):
    if node is None:
        return ""
    chunks = []
    pending = [node]
    while pending:
        current = pending.pop()
        if current.text is not None:
            chunks.append(current.text)
        else:
            pending.extend((current.right, current.left))
    return "".join(chunks)


saved = build_rope("Pump offline at bay 6")
revised = insert(saved, 4, "-47")
revised = delete(revised, 8, 16)
print("saved=", flatten(saved), sep="")
print("revised=", flatten(revised), " first=", character_at(revised, 0), sep="")
