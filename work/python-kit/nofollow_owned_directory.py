import errno
import os
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    receipt_path = Path(directory) / "receipt-47.txt"
    receipt_path.write_bytes(b"paid:47")
    (Path(directory) / "current.txt").symlink_to(receipt_path.name)
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        receipt_fd = os.open("receipt-47.txt", os.O_RDONLY | os.O_NOFOLLOW,
                             dir_fd=directory_fd)
        try:
            print("receipt", os.read(receipt_fd, 7))
        finally:
            os.close(receipt_fd)
        try:
            link_fd = os.open("current.txt", os.O_RDONLY | os.O_NOFOLLOW,
                              dir_fd=directory_fd)
        except OSError as failure:
            print("link_rejected", failure.errno in (errno.ELOOP, errno.EMLINK))
        else:
            os.close(link_fd)
            raise AssertionError("symlink unexpectedly opened")
    finally:
        os.close(directory_fd)
