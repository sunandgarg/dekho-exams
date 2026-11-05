from contextlib import contextmanager

@contextmanager
def staging_buffer(events):
    staged = []
    events.append("opened")
    try:
        yield staged
    finally:
        staged.clear()
        events.append("closed")

events = []
try:
    with staging_buffer(events) as retained:
        retained.append("R41")
        raise ValueError("import failed")
except ValueError:
    print("failure preserved")
print(events)
print(retained)
