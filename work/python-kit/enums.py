from enum import Enum, unique

@unique
class DispatchState(Enum):
    QUEUED = "queued"
    DELIVERED = "delivered"

state = DispatchState("queued")
print(state.name, state.value)
print(state == "queued")
try:
    DispatchState("QUEUE")
except ValueError:
    print("unknown wire state rejected")
