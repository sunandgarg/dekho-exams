def receipt_tags(receipt_id, tags=None):
    owned_tags = [] if tags is None else list(tags)
    owned_tags.append(receipt_id)
    return owned_tags

shared_tags = ["reviewed"]
print(receipt_tags("R41"))
print(receipt_tags("R42"))
print(receipt_tags("R43", shared_tags))
print(shared_tags)
