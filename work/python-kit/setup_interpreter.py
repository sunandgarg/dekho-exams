import sys

def supported_runtime(version):
    return version >= (3, 11)

print("runtime supported:", supported_runtime(sys.version_info[:2]))
print("old runtime supported:", supported_runtime((3, 9)))
