"""Package the checked Spring source without build output or local secrets."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
kit = root / "work/spring-kit"
archive = root / "public/downloads/aitrove-spring-source-kit.zip"
reactive = kit / "reactive-r2dbc"
batch = kit / "batch-chunks"
modulith = kit / "modulith-boundaries"
files = [kit / "README.md", kit / "pom.xml",
         *sorted(path for path in (kit / "src").rglob("*") if path.is_file()),
         reactive / "pom.xml",
         *sorted(path for path in (reactive / "src").rglob("*") if path.is_file()),
         batch / "pom.xml",
         *sorted(path for path in (batch / "src").rglob("*") if path.is_file()),
         modulith / "pom.xml",
         *sorted(path for path in (modulith / "src").rglob("*") if path.is_file())]

with ZipFile(archive, "w", ZIP_DEFLATED) as output:
    for path in files:
        info = ZipInfo("aitrove-spring-source-kit/" + path.relative_to(kit).as_posix(), date_time=(2026, 9, 29, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        output.writestr(info, path.read_bytes())

print(f"Packaged {len(files)} Spring source files: {archive}")
