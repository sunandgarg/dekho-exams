import io
import tarfile
from pathlib import PurePosixPath

archive_bytes = io.BytesIO()
with tarfile.open(fileobj=archive_bytes, mode="w") as archive:
    safe = tarfile.TarInfo("reports/quarter-47.txt")
    safe.size = 3
    archive.addfile(safe, io.BytesIO(b"47\n"))
    escape = tarfile.TarInfo("../outside.txt")
    escape.size = 0
    archive.addfile(escape, io.BytesIO())
    link = tarfile.TarInfo("reports/shortcut")
    link.type = tarfile.SYMTYPE
    link.linkname = "../outside.txt"
    archive.addfile(link)

archive_bytes.seek(0)
accepted = []
rejected = 0
with tarfile.open(fileobj=archive_bytes, mode="r:") as archive:
    for member in archive:
        name = PurePosixPath(member.name)
        if (not member.isfile() or not name.parts or name.is_absolute()
                or ".." in name.parts or name.parts[0] != "reports"):
            rejected += 1
        else:
            accepted.append(member.name)
print("accepted", accepted)
print("rejected", rejected)
