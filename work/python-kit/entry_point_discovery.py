import importlib.metadata
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "aitrove_receipt_check.py").write_text(
        "def accepted(identifier):\n    return identifier == 'R41'\n", encoding="utf-8")
    metadata = root / "aitrove_receipt_check-1.0.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: aitrove-receipt-check\nVersion: 1.0\n", encoding="utf-8")
    (metadata / "entry_points.txt").write_text(
        "[aitrove.receipts]\nvalidator = aitrove_receipt_check:accepted\n", encoding="utf-8")
    sys.path.insert(0, directory)
    try:
        distribution = next(importlib.metadata.distributions(path=[directory]))
        selected = [point for point in distribution.entry_points if point.group == "aitrove.receipts"]
        print("entry point:", selected[0].name)
        print("accepted:", selected[0].load()("R41"))
    finally:
        sys.path.remove(directory)
        sys.modules.pop("aitrove_receipt_check", None)
