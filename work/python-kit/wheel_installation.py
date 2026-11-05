from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory); project = owned / "project"; target = owned / "installed"
    package = project / "src" / "aitrove_installed_receipt"; package.mkdir(parents=True)
    (package / "__init__.py").write_text('def surcharge():\n    return 25\n', encoding="utf-8")
    (project / "pyproject.toml").write_text('[build-system]\nrequires = ["setuptools==84.0.0"]\nbuild-backend = "setuptools.build_meta"\n[project]\nname = "aitrove-installed-receipt"\nversion = "0.1.0"\n[tool.setuptools.packages.find]\nwhere = ["src"]\n', encoding="utf-8")
    subprocess.run([sys.executable, "-I", "-m", "build", "--wheel", "--no-isolation", str(project)], check=True, capture_output=True, text=True, timeout=15)
    wheel = next((project / "dist").glob("*.whl"))
    subprocess.run([sys.executable, "-I", "-m", "pip", "install", "--no-index", "--no-deps", "--no-cache-dir", "--disable-pip-version-check", "--target", str(target), str(wheel)], check=True, capture_output=True, text=True, timeout=15)
    source = 'import sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nimport aitrove_installed_receipt as receipt\nprint("installed amount:",receipt.surcharge())\nprint("installed origin:",Path(receipt.__file__).is_relative_to(Path(sys.argv[1])))\n'
    result = subprocess.run([sys.executable, "-I", "-c", source, str(target)], cwd=owned, check=True, capture_output=True, text=True, timeout=5)
    print(result.stdout.strip())
