"""Execute the published Prompt Engineering Python labs."""

import html
import json
import pathlib
import re
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
entries = {entry["path"]: entry for entry in json.loads((root / "src/data/fixtures.json").read_text())}
expected = {
    "prompt-engineering/evidence-reference-checker": "CL-291: pass\nCL-292: reject\n",
    "prompt-engineering/abstention-slice-scorer": "routine: answered=2/3 wrong=0\nhigh-impact: answered=1/2 wrong=1\n",
    "prompt-engineering/judge-order-audit": "changed: TK-482\n",
    "prompt-engineering/release-regression-gate": "release: block\ncritical_failures: CL-411\nchanged_cases: CL-411, CL-413\n",
    "prompt-engineering/candidate-sampling-and-verifier": "accepted: RN-284-C\n",
    "prompt-engineering/aggregate-denominator-reconciliation": "unique=6 late=2 rate=33.33%\n",
    "prompt-engineering/translation-glossary-placeholder-contract": "placeholder check: pass\n",
    "prompt-engineering/synthetic-case-invariants-and-oracles": "oracle: 4/4 valid\nslices: routine=1 review=2 unknown=1\n",
    "prompt-engineering/specialist-claim-merge-and-conflict-ledger": "CL-1: merge-candidate\nCL-2: merge-candidate\nCL-3: hold\n",
    "prompt-engineering/study-effect-measure-and-denominator-check": "ST-47: -7.50 percentage points\nST-88: +2.50 percentage points\n",
    "prompt-engineering/architecture-capacity-units-and-headroom-check": "peak_rps=744 healthy_workers=16 deployed_workers=17\n",
}

for path, output in expected.items():
    blocks = re.findall(r'<pre><code class="language-python">([\s\S]*?)</code></pre>', entries[path]["body"])
    assert len(blocks) == 1, path
    result = subprocess.run(
        [sys.executable, "-I", "-c", html.unescape(blocks[0])],
        text=True, capture_output=True, timeout=3, check=True,
    )
    assert result.stdout == output and not result.stderr, (path, result.stdout, result.stderr)

print(json.dumps({"passed": True, "executedLabs": len(expected)}))
