"""Link-cut forest with node-weight path sums and exact tree-edge cuts."""

from dataclasses import dataclass


@dataclass(eq=False)
class DepotNode:
    depot_id: str
    weight: int
    total: int = 0
    left: "DepotNode | None" = None
    right: "DepotNode | None" = None
    parent: "DepotNode | None" = None
    reverse_pending: bool = False

    def __post_init__(self):
        self.total = self.weight


def auxiliary_root(node: DepotNode) -> bool:
    return node.parent is None or (node.parent.left is not node and node.parent.right is not node)


def push(node: DepotNode) -> None:
    if node.reverse_pending:
        node.left, node.right = node.right, node.left
        for child in (node.left, node.right):
            if child:
                child.reverse_pending ^= True
        node.reverse_pending = False


def refresh(node: DepotNode) -> None:
    node.total = node.weight + (node.left.total if node.left else 0) + (node.right.total if node.right else 0)


def rotate(node: DepotNode) -> None:
    parent = node.parent
    grandparent = parent.parent
    if not auxiliary_root(parent):
        if grandparent.left is parent:
            grandparent.left = node
        else:
            grandparent.right = node
    node.parent = grandparent
    if parent.left is node:
        parent.left = node.right
        if node.right:
            node.right.parent = parent
        node.right = parent
    else:
        parent.right = node.left
        if node.left:
            node.left.parent = parent
        node.left = parent
    parent.parent = node
    refresh(parent)
    refresh(node)


def splay(node: DepotNode) -> None:
    ancestors = [node]
    current = node
    while not auxiliary_root(current):
        current = current.parent
        ancestors.append(current)
    for ancestor in reversed(ancestors):
        push(ancestor)
    while not auxiliary_root(node):
        parent = node.parent
        if not auxiliary_root(parent):
            grandparent = parent.parent
            if (grandparent.left is parent) == (parent.left is node):
                rotate(parent)
            else:
                rotate(node)
        rotate(node)


def access(node: DepotNode) -> None:
    previous = None
    current = node
    while current:
        splay(current)
        current.right = previous
        if previous:
            previous.parent = current
        refresh(current)
        previous = current
        current = current.parent
    splay(node)


def make_root(node: DepotNode) -> None:
    access(node)
    node.reverse_pending ^= True


def find_root(node: DepotNode) -> DepotNode:
    access(node)
    while True:
        push(node)
        if node.left is None:
            break
        node = node.left
    splay(node)
    return node


class DepotForest:
    def __init__(self, weights: dict[str, int]):
        if not weights:
            raise ValueError("at least one depot is required")
        self.nodes = {depot_id: DepotNode(depot_id, weight) for depot_id, weight in weights.items()}
        self.edges: set[frozenset[str]] = set()

    def connected(self, first_id: str, second_id: str) -> bool:
        return find_root(self.nodes[first_id]) is find_root(self.nodes[second_id])

    def link(self, first_id: str, second_id: str) -> None:
        first, second = self.nodes[first_id], self.nodes[second_id]
        if first is second or self.connected(first_id, second_id):
            raise ValueError("link would create a cycle")
        make_root(first)
        first.parent = second
        self.edges.add(frozenset((first_id, second_id)))

    def cut(self, first_id: str, second_id: str) -> None:
        edge = frozenset((first_id, second_id))
        if edge not in self.edges:
            raise KeyError("edge is not present")
        first, second = self.nodes[first_id], self.nodes[second_id]
        make_root(first)
        access(second)
        if second.left is not first or first.right is not None:
            raise AssertionError("direct edge representation was lost")
        second.left = None
        first.parent = None
        refresh(second)
        self.edges.remove(edge)

    def update(self, depot_id: str, weight: int) -> None:
        node = self.nodes[depot_id]
        access(node)
        node.weight = weight
        refresh(node)

    def path_sum(self, first_id: str, second_id: str) -> int:
        if not self.connected(first_id, second_id):
            raise ValueError("depots are disconnected")
        first, second = self.nodes[first_id], self.nodes[second_id]
        make_root(first)
        access(second)
        return second.total


forest = DepotForest({"D-19": 7, "D-26": 11, "D-47": 13, "D-61": 17})
forest.link("D-19", "D-26")
forest.link("D-26", "D-47")
print(forest.path_sum("D-19", "D-47"))
forest.cut("D-26", "D-47")
print(forest.connected("D-19", "D-47"))
forest.link("D-47", "D-61")
forest.link("D-26", "D-61")
print(forest.path_sum("D-19", "D-47"))
