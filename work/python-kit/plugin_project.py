import importlib.util
from pathlib import Path
import sys
import tempfile

def load_owned_label(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ValueError("module specification unavailable")
    module = importlib.util.module_from_spec(specification)
    if name in sys.modules: raise ValueError("module name already retained")
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
        operation = getattr(module, "receipt_label", None)
        if not callable(operation) or operation(41) != "R-0041":
            raise ValueError("plugin interface rejected")
        return operation
    except BaseException:
        sys.modules.pop(name, None)
        raise

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory)
    accepted = owned / "accepted.py"; rejected = owned / "rejected.py"
    accepted.write_text('def receipt_label(number):\n    return f"R-{number:04d}"\n', encoding="utf-8")
    rejected.write_text('receipt_label = 125\n', encoding="utf-8")
    registry = {}
    try:
        registry["minor"] = load_owned_label(accepted, "aitrove_owned_label")
        print(registry["minor"](41))
        try: registry["invalid"] = load_owned_label(rejected, "aitrove_rejected_label")
        except ValueError: print("rejected registry absent:", "invalid" not in registry)
        print("failed module absent:", "aitrove_rejected_label" not in sys.modules)
    finally:
        sys.modules.pop("aitrove_owned_label", None)
