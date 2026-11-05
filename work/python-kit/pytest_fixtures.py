from pathlib import Path
import os
import subprocess
import sys
import tempfile

TEST_SOURCE = """import pytest

def accepted_quantity(value):
    if type(value) is not int or not 0 <= value <= 8:
        raise ValueError('quantity rejected')
    return value

def test_owned_file(tmp_path):
    manifest = tmp_path / 'quantity.txt'
    manifest.write_text('3', encoding='utf-8')
    assert accepted_quantity(int(manifest.read_text(encoding='utf-8'))) == 3

@pytest.mark.parametrize('quantity', [-1, True, '3'])
def test_rejected_quantity(quantity):
    with pytest.raises(ValueError):
        accepted_quantity(quantity)
"""
with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / "test_quantity.py"
    target.write_text(TEST_SOURCE, encoding="utf-8")
    environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    result = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", str(target)],
                            cwd=directory, env=environment, capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise RuntimeError("owned pytest cases failed")
print("four owned pytest cases passed")
