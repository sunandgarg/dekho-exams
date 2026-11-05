import io
from pathlib import Path
import re
import stat
import tempfile
import zipfile

def staged_zip_members(payload):
    if not isinstance(payload, bytes) or len(payload) > 2048:
        raise ValueError("archive byte budget rejected")
    staged = {}; total = 0
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = archive.infolist()
        if len(members) > 8: raise ValueError("member budget rejected")
        for member in members:
            kind = stat.S_IFMT(member.external_attr >> 16)
            if re.fullmatch(r"[a-z][a-z0-9_-]{0,15}\.txt", member.filename) is None or member.filename in staged or kind not in (0, stat.S_IFREG):
                raise ValueError("member name or mode rejected")
            if member.file_size > 256: raise ValueError("member bytes rejected")
            with archive.open(member) as stream:
                data = stream.read(257)
            total += len(data)
            if len(data) > 256 or total > 512: raise ValueError("decompressed budget rejected")
            staged[member.filename] = data
    return staged

def owned_archive(name, content):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, content)
    return buffer.getvalue()

members = staged_zip_members(owned_archive("receipts.txt", b"R-0041\n"))
with tempfile.TemporaryDirectory() as directory:
    for name, data in members.items():
        with (Path(directory) / name).open("xb") as destination: destination.write(data)
    print("owned files:", sorted(path.name for path in Path(directory).iterdir()))
for name, content in (("../escape.txt", b"rejected"), ("receipts.txt", b"x" * 257)):
    try: staged_zip_members(owned_archive(name, content))
    except ValueError: print("archive rejected before writes")
