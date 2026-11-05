import os
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    receipt_path = Path(directory) / "receipt-47.state"
    receipt_path.write_bytes(b"ok")
    with os.scandir(directory) as entries:
        receipt_entry = next(entry for entry in entries if entry.name == receipt_path.name)
        before = receipt_entry.stat(follow_symlinks=False).st_size
        receipt_path.write_bytes(b"paid")
        cached = receipt_entry.stat(follow_symlinks=False).st_size
        fresh = os.stat(receipt_entry.path, follow_symlinks=False).st_size
    print("before", before)
    print("cached", cached)
    print("fresh", fresh)
