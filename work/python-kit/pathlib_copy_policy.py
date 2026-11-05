from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    source = Path(directory) / "current-receipt.txt"
    archived = Path(directory) / "archived-receipt.txt"
    source.write_text("batch-47", encoding="utf-8")
    copied = source.copy(archived)
    source.write_text("batch-48", encoding="utf-8")
    print("copied", copied.read_text(encoding="utf-8"))
    print("current", source.read_text(encoding="utf-8"))
