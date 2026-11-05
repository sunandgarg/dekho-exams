class RouteNode:
    def __init__(self):
        self.children = [None, None]
        self.gateway = None


class ServiceRouteTable:
    def __init__(self, width=16):
        if width < 1:
            raise ValueError("width must be positive")
        self.width = width
        self.root = RouteNode()

    def add(self, prefix, length, gateway):
        if not 0 <= length <= self.width or not 0 <= prefix < 1 << self.width:
            raise ValueError("invalid prefix or length")
        if length < self.width and prefix & ((1 << (self.width - length)) - 1):
            raise ValueError("prefix has nonzero host bits")
        node = self.root
        for offset in range(length):
            bit = (prefix >> (self.width - offset - 1)) & 1
            if node.children[bit] is None:
                node.children[bit] = RouteNode()
            node = node.children[bit]
        node.gateway = gateway

    def lookup(self, service_id):
        if not 0 <= service_id < 1 << self.width:
            raise ValueError("service ID outside configured width")
        node = self.root
        best = node.gateway
        for offset in range(self.width):
            bit = (service_id >> (self.width - offset - 1)) & 1
            node = node.children[bit]
            if node is None:
                break
            if node.gateway is not None:
                best = node.gateway
        return best


routes = ServiceRouteTable()
routes.add(0, 0, "fallback")
routes.add(0xA000, 4, "north")
routes.add(0xA900, 8, "depot")
routes.add(0xA940, 12, "pump")
print("pump=", routes.lookup(0xA947), " depot=", routes.lookup(0xA983),
      " default=", routes.lookup(0x3901), sep="")
