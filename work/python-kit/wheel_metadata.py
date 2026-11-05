import email.parser
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

with tempfile.TemporaryDirectory() as directory:
    project = Path(directory)
    (project / "pyproject.toml").write_text('[build-system]\nrequires=["setuptools==84.0.0"]\nbuild-backend="setuptools.build_meta"\n[project]\nname="aitrove-owned-receipt"\nversion="0.1.0"\nrequires-python=">=3.11"\n[tool.setuptools]\npy-modules=["receipt_value"]\n')
    (project / "receipt_value.py").write_text('AMOUNT = 125\n')
    subprocess.run([sys.executable, "-I", "-m", "build", "--wheel", "--no-isolation", str(project)], check=True, capture_output=True, timeout=20)
    artifact, = (project / "dist").glob("*.whl")
    with zipfile.ZipFile(artifact) as archive:
        metadata_name, = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        wheel_name, = [name for name in archive.namelist() if name.endswith(".dist-info/WHEEL")]
        metadata = email.parser.Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
        wheel = email.parser.Parser().parsestr(archive.read(wheel_name).decode("utf-8"))
    print("name:", metadata["Name"])
    print("version:", metadata["Version"])
    print("python:", metadata["Requires-Python"])
    print("tag:", wheel["Tag"])
