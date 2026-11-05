"""Single-writer append journal: fsync complete frames, truncate torn tail."""

import json
import os
import struct
import tempfile
import zlib
from pathlib import Path

HEADER = struct.Struct(">II")
MAX_RECORD = 1_048_576


def encode_transaction(changes):
    payload = json.dumps(changes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_RECORD:
        raise ValueError("transaction too large")
    return HEADER.pack(len(payload), zlib.crc32(payload)) + payload


def append_transaction(journal_path, changes):
    frame = encode_transaction(changes)
    with open(journal_path, "ab", buffering=0) as journal:
        written = journal.write(frame)
        if written != len(frame):
            raise OSError("short journal write")
        os.fsync(journal.fileno())


def recover(journal_path):
    pages = {}
    with open(journal_path, "r+b", buffering=0) as journal:
        while True:
            frame_start = journal.tell()
            header = journal.read(HEADER.size)
            if not header:
                break
            if len(header) < HEADER.size:
                journal.truncate(frame_start)
                os.fsync(journal.fileno())
                break
            length, checksum = HEADER.unpack(header)
            if length > MAX_RECORD:
                raise ValueError("invalid record length")
            payload = journal.read(length)
            if len(payload) < length:
                journal.truncate(frame_start)
                os.fsync(journal.fileno())
                break
            if zlib.crc32(payload) != checksum:
                raise ValueError("checksum mismatch; manual recovery required")
            changes = json.loads(payload)
            if not isinstance(changes, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in changes.items()):
                raise ValueError("invalid transaction")
            pages.update(changes)
    return pages


with tempfile.TemporaryDirectory() as temporary_directory:
    journal_path = Path(temporary_directory) / "pages.log"
    append_transaction(journal_path, {"P-19": "balanced", "P-26": "new-leaf"})
    with open(journal_path, "ab") as journal:
        journal.write(encode_transaction({"P-52": "unfinished"})[:11])
    print(recover(journal_path))
    print(journal_path.stat().st_size == len(encode_transaction({"P-19": "balanced", "P-26": "new-leaf"})))
