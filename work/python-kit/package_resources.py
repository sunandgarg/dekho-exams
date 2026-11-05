from importlib.resources import files
import importlib
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile

with tempfile.TemporaryDirectory() as directory:
    archive = Path(directory) / "receipt_regions.zip"
    with ZipFile(archive, "w") as package:
        package.writestr("receipt_regions/__init__.py", "")
        package.writestr("receipt_regions/regions.txt", "DEL\nBOM\n")
    sys.path.insert(0, str(archive))
    try:
        importlib.import_module("receipt_regions")
        text = files("receipt_regions").joinpath("regions.txt").read_text(encoding="utf-8")
        print(text.splitlines())
    finally:
        sys.path.remove(str(archive))
        sys.modules.pop("receipt_regions", None)
