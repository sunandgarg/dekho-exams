"""Sequential CAS schedule model, not a concurrent lock-free implementation."""

from dataclasses import dataclass


@dataclass
class QueueNode:
    job_id: str | None
    next_id: int | None = None


class QueueSchedule:
    def __init__(self):
        self.nodes = {0: QueueNode(None)}
        self.head_id = 0
        self.tail_id = 0
        self.next_node_id = 1

    def cas_link(self, node_id, expected_next, replacement):
        if self.nodes[node_id].next_id != expected_next:
            return False
        self.nodes[node_id].next_id = replacement
        return True

    def cas_tail(self, expected_tail, replacement):
        if self.tail_id != expected_tail:
            return False
        self.tail_id = replacement
        return True

    def cas_head(self, expected_head, replacement):
        if self.head_id != expected_head:
            return False
        self.head_id = replacement
        return True

    def offer(self, job_id):
        node_id = self.next_node_id
        self.next_node_id += 1
        self.nodes[node_id] = QueueNode(job_id)
        while True:
            tail = self.tail_id
            successor = self.nodes[tail].next_id
            if successor is not None:
                self.cas_tail(tail, successor)
            elif self.cas_link(tail, None, node_id):
                self.cas_tail(tail, node_id)
                return

    def take(self):
        while True:
            head = self.head_id
            tail = self.tail_id
            successor = self.nodes[head].next_id
            if successor is None:
                return None
            if head == tail:
                self.cas_tail(tail, successor)
                continue
            job_id = self.nodes[successor].job_id
            if self.cas_head(head, successor):
                return job_id


schedule = QueueSchedule()
stale_tail = schedule.tail_id
schedule.offer("J-47")
print(schedule.cas_link(stale_tail, None, 99))
schedule.offer("J-61")
print(schedule.take(), schedule.take(), schedule.take())
