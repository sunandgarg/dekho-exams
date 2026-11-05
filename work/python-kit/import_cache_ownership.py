import importlib
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    module_file = Path(directory) / "aitrove_owned_counter.py"
    module_file.write_text("starts = 1\n", encoding="utf-8")
    sys.path.insert(0, directory)
    importlib.invalidate_caches()
    try:
        first = importlib.import_module("aitrove_owned_counter")
        first.starts += 1
        second = importlib.import_module("aitrove_owned_counter")
        print("same object:", first is second, second.starts)
        sys.modules.pop("aitrove_owned_counter", None)
        third = importlib.import_module("aitrove_owned_counter")
        print("fresh state:", third is first, third.starts)
    finally:
        sys.modules.pop("aitrove_owned_counter", None)
        sys.path.remove(directory)
