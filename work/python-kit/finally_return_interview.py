events = []
def unsafe_result():
    try:
        raise ValueError("invalid receipt")
    finally:
        events.append("unsafe cleaned")
        return "accepted"

def safe_result():
    try:
        raise ValueError("invalid receipt")
    finally:
        events.append("safe cleaned")

print("unsafe:", unsafe_result())
try:
    safe_result()
except ValueError:
    print("safe propagated")
print("events:", events)
