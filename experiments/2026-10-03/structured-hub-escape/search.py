# Document:    Distinct Hub Escape Experiment
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      f712bed95c0cd6a48dbacb958bf5768e05f0793cc184f9c88656c93573b30b59
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Enumerate point swaps and record precisely specified heavy/hub filters."""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from covering64.core import read_blocks, verify_cover, write_blocks

ROOT = Path(__file__).parent
SOURCE = Path("experiments/2026-10-03/first-family-independent/normalized-escape-h6.txt")
blocks = list(read_blocks(SOURCE))
outside = [i for i, block in enumerate(blocks) if not set(block) & {1, 2, 3}]
attempts = qualifying = 0
best = 561
records = []
for i, j in combinations(outside, 2):
    a, b = set(blocks[i]), set(blocks[j])
    for x in sorted(a - b):
        for y in sorted(b - a):
            attempts += 1
            changed = blocks.copy()
            changed[i] = tuple(sorted(a - {x} | {y}))
            changed[j] = tuple(sorted(b - {y} | {x}))
            if len(set(changed)) != 64:
                continue
            counts = Counter(t for block in changed for t in combinations(block, 3))
            heavy = [t for t, n in counts.items() if n >= 6]
            if (max(counts.values()) > 7
                    or any(set(t) & set(u) for t, u in combinations(heavy, 2))
                    or sum(4 if counts[t] == 7 else 3 for t in heavy) > 16):
                continue
            heavy_points = set().union(*map(set, heavy))
            hubs = []
            valid = True
            for triple in heavy:
                occurrences = Counter(p for block in changed if set(triple) <= set(block)
                                      for p in block if p not in triple)
                repeated = [p for p, n in occurrences.items() if n >= 2]
                if counts[triple] == 7:
                    valid &= (len(occurrences) == 13 and len(repeated) == 1
                              and max(occurrences.values()) == 2)
                else:
                    valid &= len(repeated) <= 1 and max(occurrences.values()) <= 3
                hubs.extend(repeated)
            if (not valid or len(set(hubs)) != len(hubs) or set(hubs) & heavy_points):
                continue
            qualifying += 1
            missing = 560 - len(counts)
            if missing >= best:
                continue
            best = missing
            path = ROOT / f"candidate-h{missing}.txt"
            write_blocks(path, changed)
            package = verify_cover(changed)
            result = subprocess.run([sys.executable, "scripts/check_cover.py", str(path),
                                     "--expected-blocks", "64"], text=True, capture_output=True)
            standalone = json.loads(result.stdout)
            assert result.returncode in (0, 1)
            assert len(package["uncovered"]) == standalone["uncovered_count"] == missing
            assert Counter(p for block in changed for p in block) == Counter(
                dict.fromkeys(range(1, 17), 20))
            records.append({"path": str(path), "swap": [i, j, x, y], "hubs": hubs,
                            "heavy": [{"triple": t, "multiplicity": counts[t]} for t in heavy],
                            "package": package, "standalone": standalone})
summary = {"source": str(SOURCE), "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           "attempts": attempts, "qualifying": qualifying, "best_missing": best,
           "records": records,
           "scope": "Only the stated swap neighborhood and explicit heavy/hub filters."}
(ROOT / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "records"}))
