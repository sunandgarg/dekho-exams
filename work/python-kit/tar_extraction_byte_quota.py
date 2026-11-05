import io
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

archive_bytes = io.BytesIO()
with tarfile.open(fileobj=archive_bytes, mode="w") as archive:
    for name, payload in (
        ("reports/receipt-47.txt", b"R" * 47),
        ("reports/receipt-48.txt", b"S" * 7),
    ):
        member = tarfile.TarInfo(name)
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))

archive_bytes.seek(0)
accepted = []
rejected = 0
total_bytes = 0
with tempfile.TemporaryDirectory() as directory:
    with tarfile.open(fileobj=archive_bytes, mode="r:") as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            if (not member.isfile() or not name.parts or name.is_absolute()
                    or ".." in name.parts or name.parts[0] != "reports"
                    or total_bytes + member.size > 50):
                rejected += 1
                continue
            destination = Path(directory).joinpath(*name.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, destination.open("xb") as target:
                remaining = member.size
                while remaining:
                    chunk = source.read(min(16, remaining))
                    if not chunk:
                        raise EOFError("truncated archive member")
                    target.write(chunk)
                    remaining -= len(chunk)
            total_bytes += member.size
            accepted.append(member.name)
print("accepted", accepted)
print("rejected", rejected)
print("bytes", total_bytes)
