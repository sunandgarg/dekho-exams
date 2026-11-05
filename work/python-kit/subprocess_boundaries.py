import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-I", "-c", "import sys; print(sys.argv[1])", "$(receipt)"],
    capture_output=True, text=True, check=True, timeout=3,
)
print(result.stdout.strip())
try:
    subprocess.run([sys.executable, "-I", "-c", "raise SystemExit(3)"],
                   check=True, capture_output=True, timeout=3)
except subprocess.CalledProcessError as failure:
    print("exit:", failure.returncode)
