from pathlib import Path
from tempfile import TemporaryDirectory

owned_path = None
try:
    with TemporaryDirectory() as directory:
        owned_path = Path(directory) / "receipt.marker"
        owned_path.write_text("pending", encoding="utf-8")
        raise ValueError("invalid receipt")
except ValueError:
    print("cleaned:", not owned_path.exists())
