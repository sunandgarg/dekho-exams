import subprocess
import sys

owned_source = """
def assertion_only(amount):
    assert amount >= 0
    return amount
def validated(amount):
    if type(amount) is not int or amount < 0:
        raise ValueError("nonnegative exact integer required")
    return amount
for operation in (assertion_only, validated):
    try:
        print(operation(-25))
    except (AssertionError, ValueError) as failure:
        print(type(failure).__name__)
"""
for optimized in (False, True):
    command = [sys.executable, "-I"] + (["-O"] if optimized else [])
    output = subprocess.run(command + ["-c", owned_source], capture_output=True,
                            text=True, check=True, timeout=5).stdout.splitlines()
    print("optimized:", optimized, output)
