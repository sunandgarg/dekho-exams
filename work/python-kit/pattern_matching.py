def route_command(command):
    if not isinstance(command, dict) or set(command) != {"operation", "receipt_id"}:
        raise ValueError("command shape")
    match command:
        case {"operation": "read", "receipt_id": identifier} if type(identifier) is int and identifier > 0:
            return f"read:{identifier}"
        case _:
            raise ValueError("command rejected")

print(route_command({"operation": "read", "receipt_id": 41}))
for command in [{"operation": "read", "receipt_id": True}, {"operation": "read", "receipt_id": 41, "tenant": "a"}]:
    try:
        route_command(command)
    except ValueError:
        print("command rejected")
