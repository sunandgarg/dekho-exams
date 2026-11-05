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


for bay_key in (47, 52, 61, 19, 26, 58, 83, 31, 67, 73):
    bay_root = insert(bay_root, bay_key)
print(ordered(bay_root))
print(contains(bay_root, 58), contains(bay_root, 49))
