import mmap
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    receipt_path = Path(directory) / "receipt-47.state"
    receipt_path.write_bytes(b"R-0047:hold")
    with receipt_path.open("r+b") as receipt_file:
        with mmap.mmap(receipt_file.fileno(), 0, access=mmap.ACCESS_WRITE) as view:
            view[7:11] = b"paid"
            view.flush()
        with mmap.mmap(receipt_file.fileno(), 0, access=mmap.ACCESS_COPY) as private_view:
            private_view[7:11] = b"void"
            print("private", bytes(private_view[:]))
    print("stored", receipt_path.read_bytes())
