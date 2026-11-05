from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    report = Path(directory) / "receipt-41.txt"
    report.write_text("amount_minor=125\n", encoding="utf-8")
    print("name:", report.name)
    print("suffix:", report.suffix)
    print("content:", report.read_text(encoding="utf-8").strip())
    print("missing:", (Path(directory) / "receipt-42.txt").exists())
