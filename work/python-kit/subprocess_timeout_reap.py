import subprocess
import sys

child = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(1)"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
try:
    child.communicate(timeout=0.02)
    timed_out = False
except subprocess.TimeoutExpired:
    timed_out = True
    child.kill()
    child.communicate()
print("timed_out", timed_out)
print("reaped", child.returncode is not None)
