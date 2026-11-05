# Python operational-boundary editorial note — 2026-10-01

Internal verification only. The five requested reference links are Java LinkedList pages, so they do not establish Python behavior. The published article bodies use original explanations and local fixtures without external URLs.

Technical checks:

- Python subprocess `communicate`, timeout behavior, output buffering and cleanup: https://docs.python.org/3.13/library/subprocess.html
- Client TLS context, certificate and hostname settings: https://docs.python.org/3.13/library/ssl.html
- SQLite `executescript` pending-transaction behavior: https://docs.python.org/3.13/library/sqlite3.html
- JSON `object_pairs_hook` and duplicate name behavior: https://docs.python.org/3.13/library/json.html
- Tar extraction filters, links, partial extraction and resource limits: https://docs.python.org/3.13/library/tarfile.html
- Same-filesystem replacement and filesystem semantics: https://docs.python.org/3.13/library/os.html and https://docs.python.org/3.13/library/tempfile.html

The source kit executes all eight new programs and compares exact output through `scripts/check-python-content.py`. The subprocess output fixture demonstrates post-run rejection, not a hard streaming quota. The TLS fixture inspects settings without a handshake. The tar fixture performs metadata preflight without extraction. The replacement fixture shows pathname visibility, not power-loss durability. Do not widen those claims without integration checks.

Further open work includes a process-tree shutdown test for the target operating systems, a true streaming output cap with backpressure, a local TLS handshake with accepted and rejected certificates, a disk-backed migration rehearsal over realistic data, archive extraction in a fresh directory with measured byte quotas, and browser review of the new lesson and quiz layouts.
