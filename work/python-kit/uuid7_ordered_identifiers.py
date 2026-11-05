import uuid

first_order_id = uuid.uuid7()
second_order_id = uuid.uuid7()
print("versions", first_order_id.version, second_order_id.version)
print("distinct", first_order_id != second_order_id)
print("time_non_decreasing", first_order_id.time <= second_order_id.time)
