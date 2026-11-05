class RouteNode:
    def __init__(self, prefix, destination=None):
        self.prefix = prefix
        self.destination = destination
        self.children = {}


class PatriciaRouteIndex:
    def __init__(self, width=8):
        if width < 1:
            raise ValueError("positive bit width required")
        self.width = width
        self.root = RouteNode("")

    def _bits(self, address):
        if not 0 <= address < 1 << self.width:
            raise ValueError("address outside configured width")
        return format(address, f"0{self.width}b")

    def insert(self, network, prefix_length, destination):
        if not 0 <= prefix_length <= self.width:
            raise ValueError("invalid prefix length")
        target = self._bits(network)[:prefix_length]
        node = self.root
        while True:
            if node.prefix == target:
                node.destination = destination
                return
            branch = target[len(node.prefix)]
            child = node.children.get(branch)
            if child is None:
                node.children[branch] = RouteNode(target, destination)
                return
            common = len(node.prefix)
            while common < min(len(child.prefix), len(target)) and child.prefix[common] == target[common]:
                common += 1
            if common == len(child.prefix):
                node = child
                continue
            split = RouteNode(target[:common])
            node.children[branch] = split
            split.children[child.prefix[common]] = child
            if common == len(target):
                split.destination = destination
            else:
                split.children[target[common]] = RouteNode(target, destination)
            return

    def longest_match(self, address):
        bits = self._bits(address)
        node = self.root
        answer = node.destination
        while len(node.prefix) < self.width:
            child = node.children.get(bits[len(node.prefix)])
            if child is None or bits[len(node.prefix):len(child.prefix)] != child.prefix[len(node.prefix):]:
                break
            node = child
            if node.destination is not None:
                answer = node.destination
        return answer


routes = PatriciaRouteIndex()
routes.insert(0, 0, "default-gateway")
routes.insert(176, 5, "north-depot")
routes.insert(184, 5, "south-depot")
routes.insert(160, 3, "regional-gateway")
print(routes.longest_match(178), routes.longest_match(190))
print(routes.longest_match(171), routes.longest_match(132))
routes.insert(176, 5, "north-backup")
print(routes.longest_match(178))
