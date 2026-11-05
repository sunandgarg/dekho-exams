from bisect import bisect_left, bisect_right


class BayPage:
    def __init__(self, leaf):
        self.leaf = leaf
        self.keys = []
        self.children = []
        self.next_page = None


maximum_keys = 3
bay_root = BayPage(True)


def add_to_page(page, bay_key):
    if page.leaf:
        position = bisect_left(page.keys, bay_key)
        if position < len(page.keys) and page.keys[position] == bay_key:
            return None
        page.keys.insert(position, bay_key)
        if len(page.keys) <= maximum_keys:
            return None
        split_at = (len(page.keys) + 1) // 2
        right = BayPage(True)
        right.keys = page.keys[split_at:]
        page.keys = page.keys[:split_at]
        right.next_page, page.next_page = page.next_page, right
        return right.keys[0], right

    position = bisect_right(page.keys, bay_key)
    split = add_to_page(page.children[position], bay_key)
    if split is None:
        return None
    separator, right_child = split
    page.keys.insert(position, separator)
    page.children.insert(position + 1, right_child)
    if len(page.keys) <= maximum_keys:
        return None
    middle = len(page.keys) // 2
    right = BayPage(False)
    right.keys = page.keys[middle + 1:]
    right.children = page.children[middle + 1:]
    separator = page.keys[middle]
    page.keys = page.keys[:middle]
    page.children = page.children[:middle + 1]
    return separator, right


def insert(root, bay_key):
    split = add_to_page(root, bay_key)
    if split is None:
        return root
    separator, right_child = split
    promoted = BayPage(False)
    promoted.keys = [separator]
    promoted.children = [root, right_child]
    return promoted


def contains(root, bay_key):
    page = root
    while not page.leaf:
        page = page.children[bisect_right(page.keys, bay_key)]
    position = bisect_left(page.keys, bay_key)
    return position < len(page.keys) and page.keys[position] == bay_key


def ordered(root):
    page = root
    while not page.leaf:
        page = page.children[0]
    result = []
    while page is not None:
        result.extend(page.keys)
        page = page.next_page
    return result


def smallest(page):
    while not page.leaf:
        page = page.children[0]
    return page.keys[0]


def refresh_separators(page):
    if not page.leaf:
        page.keys = [smallest(child) for child in page.children[1:]]


def remove(root, bay_key):
    page = root
    path = []
    while not page.leaf:
        position = bisect_right(page.keys, bay_key)
        path.append((page, position))
        page = page.children[position]
    position = bisect_left(page.keys, bay_key)
    if position == len(page.keys) or page.keys[position] != bay_key:
        return root, False
    page.keys.pop(position)

    for parent, position in reversed(path):
        minimum = 2 if page.leaf else 2
        size = len(page.keys) if page.leaf else len(page.children)
        if size < minimum:
            left = parent.children[position - 1] if position else None
            right = parent.children[position + 1] if position + 1 < len(parent.children) else None
            left_size = (len(left.keys) if left.leaf else len(left.children)) if left else 0
            right_size = (len(right.keys) if right.leaf else len(right.children)) if right else 0
            if left_size > minimum:
                if page.leaf:
                    page.keys.insert(0, left.keys.pop())
                else:
                    page.children.insert(0, left.children.pop())
                    refresh_separators(left)
                    refresh_separators(page)
            elif right_size > minimum:
                if page.leaf:
                    page.keys.append(right.keys.pop(0))
                else:
                    page.children.append(right.children.pop(0))
                    refresh_separators(right)
                    refresh_separators(page)
            elif left:
                if page.leaf:
                    left.keys.extend(page.keys)
                    left.next_page = page.next_page
                else:
                    left.children.extend(page.children)
                    refresh_separators(left)
                parent.children.pop(position)
            else:
                if page.leaf:
                    page.keys.extend(right.keys)
                    page.next_page = right.next_page
                else:
                    page.children.extend(right.children)
                    refresh_separators(page)
                parent.children.pop(position + 1)
        refresh_separators(parent)
        page = parent

    while not root.leaf and len(root.children) == 1:
        root = root.children[0]
    return root, True


for bay_key in (47, 52, 61, 19, 26, 58, 83, 31, 67, 73):
    bay_root = insert(bay_root, bay_key)
for bay_key in (19, 26, 31, 47, 52, 58):
    bay_root, removed = remove(bay_root, bay_key)
    assert removed
print(ordered(bay_root))
print(remove(bay_root, 49)[1], contains(bay_root, 61))
