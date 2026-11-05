import base64
import csv
import hashlib
import io
import zipfile

def archive_for(source):
    digest = base64.urlsafe_b64encode(hashlib.sha256(b"owner = 'aitrove'\n").digest()).rstrip(b"=").decode("ascii")
    record = f"receipt_tools.py,sha256={digest},18\n"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as wheel:
        wheel.writestr("receipt_tools.py", source)
        wheel.writestr("receipt_tools-1.0.dist-info/RECORD", record)
    return output.getvalue()

def declared_module_matches(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as wheel:
        rows = list(csv.reader(io.StringIO(wheel.read("receipt_tools-1.0.dist-info/RECORD").decode("utf-8"))))
        if len(rows) != 1 or rows[0][0] != "receipt_tools.py" or len(rows[0]) != 3 or wheel.namelist().count("receipt_tools.py") != 1:
            raise ValueError("record shape")
        digest = base64.urlsafe_b64encode(hashlib.sha256(wheel.read("receipt_tools.py")).digest()).rstrip(b"=").decode("ascii")
        return rows[0][1] == "sha256=" + digest and rows[0][2] == str(len(wheel.read("receipt_tools.py")))

print("owned bytes:", declared_module_matches(archive_for(b"owner = 'aitrove'\n")))
print("altered bytes:", declared_module_matches(archive_for(b"owner = 'other'\n")))
