import os
import tempfile
from pathlib import Path

def publish_report(target, amounts):
    if len(amounts) > 32 or any(type(amount) is not int or not 0 <= amount <= 1000000 for amount in amounts):
        raise ValueError("report amounts")
    candidate = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as output:
            candidate = Path(output.name)
            output.write("total_minor=" + str(sum(amounts)) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(candidate, target)
    finally:
        if candidate is not None:
            candidate.unlink(missing_ok=True)

with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / "report.txt"
    publish_report(target, [125, 75])
    try:
        publish_report(target, [125, True])
    except ValueError:
        print("invalid report rejected")
    print(target.read_text(encoding="utf-8").strip())
