from pathlib import Path
import subprocess
import sys
import tempfile
import zipapp
from zipfile import ZipFile

with tempfile.TemporaryDirectory() as directory:
    application = Path(directory) / "receipt_cli"
    application.mkdir()
    (application / "__main__.py").write_text(
        'import sys\n'
        'if len(sys.argv) != 2 or sys.argv[1] != "--region-count":\n'
        '    raise SystemExit(2)\n'
        'print("supported regions: 2")\n', encoding="utf-8")
    archive = Path(directory) / "receipt_cli.pyz"
    zipapp.create_archive(application, archive, compressed=True)
    result = subprocess.run([sys.executable, "-I", str(archive), "--region-count"],
                            cwd=directory, capture_output=True, text=True, timeout=5, check=True)
    print(result.stdout.strip())
    with ZipFile(archive) as built:
        print("archive built:", "__main__.py" in built.namelist())
