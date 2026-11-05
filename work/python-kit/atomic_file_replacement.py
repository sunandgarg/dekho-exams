import os
import pathlib
import tempfile

with tempfile.TemporaryDirectory() as directory:
    target = pathlib.Path(directory) / "receipt-index.txt"
    target.write_text("revision 46\n")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=directory,
        prefix=".receipt-index-", delete=False,
    ) as draft:
        draft.write("revision 47\n")
        draft.flush()
        os.fsync(draft.fileno())
        draft_name = draft.name
    try:
        os.replace(draft_name, target)
    finally:
        if os.path.exists(draft_name):
            os.unlink(draft_name)
    print(target.read_text().strip())
    print("target_exists", target.exists())
