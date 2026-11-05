from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory); project = owned / "project"; target = owned / "installed"
    package = project / "src" / "aitrove_editable_receipt"; package.mkdir(parents=True)
    module = package / "__init__.py"
    module.write_text('def fee():\n    return 25\n', encoding="utf-8")
    (project / "pyproject.toml").write_text('[build-system]\nrequires = ["setuptools==84.0.0"]\nbuild-backend = "setuptools.build_meta"\n[project]\nname = "aitrove-editable-receipt"\nversion = "0.1.0"\n[tool.setuptools.packages.find]\nwhere = ["src"]\n', encoding="utf-8")
    subprocess.run([sys.executable, "-I", "-m", "pip", "install", "--no-index", "--no-deps", "--no-build-isolation", "--no-cache-dir", "--disable-pip-version-check", "--target", str(target), "-e", str(project)], check=True, capture_output=True, text=True, timeout=20)
    def installed_fee():
        result = subprocess.run([sys.executable, "-I", "-B", "-c", 'import site,sys; site.addsitedir(sys.argv[1]); import aitrove_editable_receipt; print(aitrove_editable_receipt.fee())', str(target)], cwd=owned, check=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    print("first process:", installed_fee())
    module.write_text('def fee():\n    return 125\n', encoding="utf-8")
    print("fresh process after edit:", installed_fee())
