from compression import zstd

receipt_payload = b"R" * 47000
frame = zstd.compress(receipt_payload)
decoder = zstd.ZstdDecompressor()
prefix = decoder.decompress(frame, max_length=4097)
print("over_budget", len(prefix) > 4096)
print("complete_frame", decoder.eof)
