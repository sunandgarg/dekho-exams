class FailureGuard:
    def __init__(self, suppress=False):
        self.suppress = suppress
        self.seen = []
    def __enter__(self):
        return self
    def __exit__(self, failure_type, failure, traceback):
        self.seen.append(None if failure_type is None else failure_type.__name__)
        return self.suppress and failure_type is ValueError

strict = FailureGuard()
try:
    with strict:
        raise ValueError("invalid receipt")
except ValueError:
    print("strict propagated:", strict.seen)
soft = FailureGuard(suppress=True)
with soft:
    raise ValueError("invalid receipt")
print("soft continued:", soft.seen)
