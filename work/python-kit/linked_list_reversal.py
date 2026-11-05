class DispatchNode:
    def __init__(self, receipt_id, next_node=None):
        self.receipt_id = receipt_id
        self.next = next_node

def reverse_chain(head):
    seen, current = set(), head
    while current is not None:
        if type(current) is not DispatchNode or id(current) in seen or len(seen) == 64:
            raise ValueError("cycle, node type or chain budget")
        seen.add(id(current)); current = current.next
    previous, current = None, head
    while current is not None:
        successor = current.next
        current.next = previous
        previous, current = current, successor
    return previous

head = DispatchNode(41, DispatchNode(42, DispatchNode(43)))
old_head = head
head = reverse_chain(head)
values = []
while head is not None:
    values.append(head.receipt_id); head = head.next
print(values)
print(old_head.next is None)
