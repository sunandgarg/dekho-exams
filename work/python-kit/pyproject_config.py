import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    project = Path(directory)
    package = project / "src" / "aitrove_receipts"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('def amount_unit():\n    return "minor"\n', encoding="utf-8")
    (project / "pyproject.toml").write_text("""[build-system]
requires = ["setuptools==84.0.0"]
build-backend = "setuptools.build_meta"
[project]
name = "aitrove-receipt-fixture"
version = "0.1.0"
requires-python = ">=3.11"
[tool.setuptools.packages.find]
where = ["src"]
""", encoding="utf-8")
    subprocess.run([sys.executable, "-I", "-m", "build", "--wheel", "--no-isolation", str(project)],
                   check=True, capture_output=True, text=True, timeout=10)
    wheel = next((project / "dist").glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata = archive.read(next(name for name in names if name.endswith("/METADATA"))).decode("utf-8")
        print("module included:", "aitrove_receipts/__init__.py" in names)
        print("Python metadata:", "Requires-Python: >=3.11" in metadata)
