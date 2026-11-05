from contextlib import ExitStack

def acquire_bundle(events, fail=False):
    with ExitStack() as pending:
        pending.callback(events.append, "stream released")
        pending.callback(events.append, "index released")
        if fail:
            raise ValueError("index validation")
        return pending.pop_all()

events = []
owner = acquire_bundle(events)
print("before close:", events)
owner.close()
owner.close()
print("after close:", events)
failed_events = []
try:
    acquire_bundle(failed_events, fail=True)
except ValueError:
    print("failed setup:", failed_events)
