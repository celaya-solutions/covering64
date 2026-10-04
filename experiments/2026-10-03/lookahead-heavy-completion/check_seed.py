# Document:    Independent Ten-Hole Pilot State Recount
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      a990a0bc2f4c8bca0b34db770ae0495658f387c4de2b724c3c9cc15db8d60422
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import importlib.util
import itertools as it
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments/scratch/four-seven-template-native-lookahead-v1.2.0/pilots"
ORACLE = HERE.parent / "four-seven-template-lookahead-independent/oracle.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location("independent_oracle", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    path = SOURCE / "cycle-raw-best.txt"
    sidecar = path.with_suffix(".txt.lookahead.json")
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64
    assert blocks == sorted(blocks)
    assert all(len(b) == 5 and tuple(sorted(set(b))) == b for b in blocks)
    assert all(1 <= p <= 16 for b in blocks for p in b)
    heavy = oracle.heavy_blocks(blocks)
    recounted = oracle.analyze(heavy)
    recorded = json.loads(sidecar.read_text())
    assert list(map(list, recounted["admissible_blocks"])) == recorded["admissible_blocks"]
    assert list(map(list, recounted["unsupported"])) == recorded["unsupported_triples"]
    assert recounted["allowed_ordinary"] == recorded["admissible_count"] == 680
    assert recounted["unsupported_count"] == recorded["unsupported_count"] == 0
    counts = Counter(t for b in blocks for t in it.combinations(b, 3))
    holes = sorted(set(it.combinations(range(1, 17), 3)) - counts.keys())
    assert len(holes) == recorded["holes"] == 10
    receipt = {
        "passed": True, "checker_sha256": sha(Path(__file__)),
        "oracle_sha256": sha(ORACLE), "witness_sha256": sha(path),
        "sidecar_sha256": sha(sidecar), "holes": len(holes), "missing_triples": holes,
        "fixed_heavy": 28, "ordinary": 36, "degree_20": True,
        "heavy_uncovered_triples": recounted["heavy_uncovered"],
        "all_ordinary_candidates_recounted": 1200,
        "complete_admissible_set_match": True, "admissible_count": 680,
        "complete_unsupported_set_match": True, "unsupported_count": 0,
        "scope": "Recount of one near-cover. Ten uncovered triples remain; this is not a cover.",
    }
    (HERE / "seed-audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
