import importlib.util
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory, "receipt_policy.py")
    owned.write_text("def limit():\n    return 500\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("aitrove_owned_receipt_policy", owned)
    if spec is None or spec.loader is None or Path(spec.origin).resolve() != owned.resolve():
        raise ValueError("unexpected module origin")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("owned origin:", Path(spec.origin).resolve() == owned.resolve())
    print("limit:", module.limit())
