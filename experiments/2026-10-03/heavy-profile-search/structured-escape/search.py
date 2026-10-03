# Document:    Structured Heavy Pattern Escape
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      98a1f947444beb9c437bf58f67b24b8834e6a00c3d5af18fc5cf6edde7908778
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check every two-block point swap among the eighteen outside blocks."""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from covering64.core import read_blocks, verify_cover, write_blocks

ROOT = Path(__file__).parent
SOURCE = Path("experiments/2026-10-03/reduced-family-heuristic/trades-2026100362/"
              "search-improvement-24-h5.txt")
blocks = list(read_blocks(SOURCE))
outside = [i for i, b in enumerate(blocks) if not set(b) & {1, 2, 3}]
assert len(outside) == 18
original_counts = Counter(t for b in blocks for t in combinations(b, 3))
best = 561
attempts = qualifying = 0
records = []
for i, j in combinations(outside, 2):
    a, b = set(blocks[i]), set(blocks[j])
    for x in sorted(a - b):
        for y in sorted(b - a):
            attempts += 1
            new_a, new_b = tuple(sorted(a - {x} | {y})), tuple(sorted(b - {y} | {x}))
            changed = blocks.copy()
            changed[i], changed[j] = new_a, new_b
            if len(set(changed)) != 64:
                continue
            counts = original_counts.copy()
            for old in (blocks[i], blocks[j]):
                counts.subtract(combinations(old, 3))
            for new in (new_a, new_b):
                counts.update(combinations(new, 3))
            heavy = [t for t, n in counts.items() if n >= 6]
            if (max(counts.values()) > 7
                    or any(set(t) & set(u) for t, u in combinations(heavy, 2))
                    or sum(4 if counts[t] == 7 else 3 for t in heavy) > 16):
                continue
            qualifying += 1
            missing = 560 - sum(n > 0 for n in counts.values())
            if missing >= best:
                continue
            best = missing
            path = ROOT / f"candidate-h{missing}.txt"
            write_blocks(path, changed)
            package = verify_cover(changed)
            result = subprocess.run([sys.executable, "scripts/check_cover.py", str(path),
                                     "--expected-blocks", "64"], capture_output=True, text=True)
            standalone = json.loads(result.stdout)
            assert result.returncode in (0, 1)
            assert len(package["uncovered"]) == standalone["uncovered_count"] == missing
            degrees = Counter(p for block in changed for p in block)
            assert degrees == Counter(dict.fromkeys(range(1, 17), 20))
            records.append({"path": str(path), "package": package, "standalone": standalone,
                            "swap": {"block_indices": [i, j], "points": [x, y]},
                            "heavy": [{"triple": t, "multiplicity": counts[t]} for t in heavy]})
summary = {"source": str(SOURCE), "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           "attempts": attempts, "qualifying": qualifying, "best_missing": best,
           "records": records,
           "scope": "Only the stated two-outside-block point-swap neighborhood."}
(ROOT / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "records"}))
