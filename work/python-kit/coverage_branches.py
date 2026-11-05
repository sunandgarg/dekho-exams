from pathlib import Path
import importlib.util
import json
import tempfile
import coverage

with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / "quantity_rules.py"
    target.write_text('def accept_quantity(quantity):\n    if quantity < 0:\n        raise ValueError("negative")\n    return quantity\n', encoding="utf-8")
    measured = coverage.Coverage(branch=True, data_file=str(Path(directory) / ".coverage"))
    measured.start()
    try:
        spec = importlib.util.spec_from_file_location("owned_quantity_rules", target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.accept_quantity(3) == 3
        try:
            module.accept_quantity(-1)
        except ValueError:
            pass
        else:
            raise AssertionError("negative branch did not reject")
    finally:
        measured.stop()
    report = Path(directory) / "coverage.json"
    measured.json_report(outfile=str(report), include=[str(target)])
    details = json.loads(report.read_text(encoding="utf-8"))
    print("missing branches:", details["totals"]["missing_branches"])
print("measurement files owned by temporary directory")
