class DispatchOrder:
    GAP = 16

    def __init__(self, task_ids):
        if len(set(task_ids)) != len(task_ids):
            raise ValueError("duplicate task")
        self.tasks = list(task_ids)
        self.labels = {task: (position + 1) * self.GAP for position, task in enumerate(self.tasks)}
        self.relabels = 0

    def before(self, first, second):
        return self.labels[first] < self.labels[second]

    def _relabel(self):
        self.labels = {task: (position + 1) * self.GAP for position, task in enumerate(self.tasks)}
        self.relabels += 1

    def insert_after(self, anchor, task):
        if task in self.labels:
            raise ValueError("duplicate task")
        position = self.tasks.index(anchor) + 1
        left = self.labels[anchor]
        right = self.labels[self.tasks[position]] if position < len(self.tasks) else left + self.GAP
        if right - left <= 1:
            self._relabel()
            left = self.labels[anchor]
            right = self.labels[self.tasks[position]] if position < len(self.tasks) else left + self.GAP
        self.tasks.insert(position, task)
        self.labels[task] = (left + right) // 2

    def remove(self, task):
        self.tasks.remove(task)
        del self.labels[task]


if __name__ == "__main__":
    queue = DispatchOrder(["T-19", "T-83"])
    for task in ["T-47", "T-52", "T-61", "T-67", "T-71"]:
        queue.insert_after("T-19", task)
    print(queue.tasks)
    print(queue.before("T-19", "T-83"), queue.relabels)
