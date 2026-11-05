import argparse

parser = argparse.ArgumentParser(prog="receiptctl", add_help=False)
commands = parser.add_subparsers(dest="command", required=True)
reconcile = commands.add_parser("reconcile", add_help=False)
reconcile.add_argument("--tenant", required=True)
reconcile.add_argument("--limit", type=int, required=True)
arguments = parser.parse_args([
    "reconcile", "--tenant", "north-47", "--limit", "47"
])
if not 1 <= arguments.limit <= 500:
    raise ValueError("limit outside accepted range")
print(arguments.command, arguments.tenant, arguments.limit)
