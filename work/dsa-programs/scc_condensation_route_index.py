class CondensedRoutes:
    def __init__(self, vertex_count, directed_edges):
        if vertex_count < 0:
            raise ValueError("negative vertex count")
        self.count = vertex_count
        self.forward = [[] for _ in range(vertex_count)]
        reverse = [[] for _ in range(vertex_count)]
        for source, target in directed_edges:
            if not (0 <= source < vertex_count and 0 <= target < vertex_count):
                raise ValueError("edge outside graph")
            self.forward[source].append(target)
            reverse[target].append(source)
        visited, finish = set(), []
        for source in range(vertex_count):
            if source in visited:
                continue
            stack = [(source, False)]
            while stack:
                vertex, completed = stack.pop()
                if completed:
                    finish.append(vertex)
                elif vertex not in visited:
                    visited.add(vertex)
                    stack.append((vertex, True))
                    stack.extend((neighbor, False) for neighbor in self.forward[vertex] if neighbor not in visited)
        self.component = [-1] * vertex_count
        component_count = 0
        for source in reversed(finish):
            if self.component[source] != -1:
                continue
            pending = [source]
            self.component[source] = component_count
            while pending:
                vertex = pending.pop()
                for neighbor in reverse[vertex]:
                    if self.component[neighbor] == -1:
                        self.component[neighbor] = component_count
                        pending.append(neighbor)
            component_count += 1
        self.dag = [set() for _ in range(component_count)]
        for source in range(vertex_count):
            for target in self.forward[source]:
                first, second = self.component[source], self.component[target]
                if first != second:
                    self.dag[first].add(second)
        self.reachable_components = []
        for source in range(component_count):
            seen, pending = {source}, [source]
            while pending:
                for target in self.dag[pending.pop()]:
                    if target not in seen:
                        seen.add(target)
                        pending.append(target)
            self.reachable_components.append(seen)

    def reaches(self, source, target):
        if not (0 <= source < self.count and 0 <= target < self.count):
            raise ValueError("vertex outside graph")
        return self.component[target] in self.reachable_components[self.component[source]]


if __name__ == "__main__":
    index = CondensedRoutes(7, [(0, 1), (1, 2), (2, 0), (2, 3),
                                (3, 4), (4, 3), (4, 5)])
    print(len(index.dag), index.reaches(1, 5), index.reaches(5, 1))
    print(index.component[0] == index.component[2], index.component[3] == index.component[4])
