import subprocess
import sys

child = subprocess.Popen(
    [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'R' * 47000)"],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)
prefix = child.stdout.read(4097)
too_large = len(prefix) > 4096
if too_large:
    child.kill()
child.stdout.close()
child.wait(timeout=5)
print("too_large", too_large)
print("reaped", child.returncode is not None)
