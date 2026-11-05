from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    record_path = Path(directory) / "receipt.txt"
    record_path.write_text("amount=125", encoding="utf-8")
    with record_path.open(encoding="utf-8") as handle:
        print(handle.read())
    print(record_path.name)
