import subprocess
import sys
import tempfile

with tempfile.TemporaryFile() as report_output:
    completed = subprocess.run(
        [sys.executable, "-c", "import sys; sys.stdout.write('R' * 47000)"],
        stdout=report_output,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=5,
    )
    report_output.seek(0, 2)
    byte_count = report_output.tell()
    print("exit", completed.returncode)
    print("bytes", byte_count)
    print("accepted", byte_count <= 4096)
