import sys
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    observed_opens = []

    def record_open(event, arguments):
        if event == "open":
            observed_opens.append(event)

    sys.addaudithook(record_open)
    receipt_file = Path(directory) / "receipt-47.txt"
    receipt_file.write_text("paid", encoding="utf-8")
    print("observed_open", bool(observed_opens))
