import subprocess
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    source_root = Path(directory) / "src"
    package = source_root / "aitrove_receipts"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "amounts.py").write_text('def label(amount):\n    return f"minor={amount}"\n', encoding="utf-8")
    (package / "__main__.py").write_text('from .amounts import label\nprint(label(125))\n', encoding="utf-8")
    launcher = "import sys, runpy; sys.path.insert(0, sys.argv[1]); runpy.run_module('aitrove_receipts', run_name='__main__')"
    result = subprocess.run([sys.executable, "-I", "-c", launcher, str(source_root)],
                            check=True, capture_output=True, text=True, timeout=3)
    print(result.stdout.strip())
