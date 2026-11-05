from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory)
    accepted = owned / "accepted.py"
    rejected = owned / "rejected.py"
    accepted.write_text("def receipt_amount() -> int:\n    return 125\n", encoding="utf-8")
    rejected.write_text("def receipt_amount() -> int:\n    return '125'\n", encoding="utf-8")
    command = [sys.executable, "-I", "-m", "mypy", "--strict", "--python-version", "3.11",
               "--no-incremental", "--cache-dir", str(owned / "cache")]
    good = subprocess.run(command + [str(accepted)], cwd=directory, capture_output=True, text=True, timeout=10)
    bad = subprocess.run(command + [str(rejected)], cwd=directory, capture_output=True, text=True, timeout=10)
    if good.returncode != 0 or bad.returncode != 1 or "[return-value]" not in bad.stdout:
        raise RuntimeError("unexpected type-check result")
print("valid return accepted")
print("text return rejected by static check")
