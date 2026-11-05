import ast
import subprocess
import sys

source = 'receipt_amounts = [125, 250, 75]\nprint(sum(receipt_amounts))\n'
ast.parse(source, feature_version=(3, 11))
print("3.11 grammar accepted")
result = subprocess.run([sys.executable, "-I", "-c", source], check=True, capture_output=True, text=True, timeout=5)
assert result.stdout == "450\n"
print("executed output:", result.stdout.strip())
print("executed runtime:", sys.version.split()[0])
