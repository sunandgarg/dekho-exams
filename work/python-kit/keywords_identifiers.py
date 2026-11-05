import keyword
import re

print("reserved:", keyword.iskeyword("class"))
print("valid spelling:", "class".isidentifier())
namespace = {}
exec(compile("match = 125", "owned-source", "exec"), namespace)
print("soft keyword value:", namespace["match"])
try:
    compile("class = 125", "owned-source", "exec")
except SyntaxError:
    print("reserved assignment rejected")
print("wire accepted:", re.fullmatch(r"[A-Z][A-Z0-9_]{0,15}", "RECEIPT_41") is not None)
