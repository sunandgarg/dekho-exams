import importlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

with tempfile.TemporaryDirectory() as directory:
    Path(directory, "aitrove_clock_source.py").write_text("def time_value():\n    return 10\n", encoding="utf-8")
    Path(directory, "aitrove_clock_consumer.py").write_text("from aitrove_clock_source import time_value\ndef read():\n    return time_value()\n", encoding="utf-8")
    sys.path.insert(0, directory)
    importlib.invalidate_caches()
    try:
        source = importlib.import_module("aitrove_clock_source")
        consumer = importlib.import_module("aitrove_clock_consumer")
        with patch.object(source, "time_value", return_value=20):
            print("source patch:", consumer.read())
        with patch.object(consumer, "time_value", return_value=30):
            print("consumer patch:", consumer.read())
    finally:
        for name in ("aitrove_clock_consumer", "aitrove_clock_source"):
            sys.modules.pop(name, None)
        sys.path.remove(directory)
