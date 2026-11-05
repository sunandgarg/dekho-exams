handled = []
try:
    try:
        raise ExceptionGroup("receipt import failures", [ValueError("quantity"), OSError("input file")])
    except* ValueError as selected:
        handled.extend(type(failure).__name__ for failure in selected.exceptions)
except ExceptionGroup as remaining:
    print("remaining:", [type(failure).__name__ for failure in remaining.exceptions])
print("handled:", handled)
