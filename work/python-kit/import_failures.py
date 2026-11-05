from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory)
    (owned / "aitrove_failed_import.py").write_text('from pathlib import Path\nPath(__file__).with_suffix(".marker").write_text("started")\nraise RuntimeError("initialization failed")\n', encoding="utf-8")
    source = r'''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
try:
    import aitrove_failed_import
except RuntimeError:
    print("failed module retained:", "aitrove_failed_import" in sys.modules)
print("side effect retained:", (Path(sys.argv[1]) / "aitrove_failed_import.marker").exists())'''
    result = subprocess.run([sys.executable, "-I", "-c", source, str(owned)], capture_output=True, text=True, check=True, timeout=5)
    print(result.stdout.strip())
