# Document:    Archived Partition and Inversive Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b71dafbf26044f6bf12d8015bc1c0484efbe520421adb65e41911e270bf5289a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import importlib.util
import json
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "reader", ROOT / "scripts/check_independent_clebsch.py"
)
READER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(READER)
BLOCKS = list(combinations(range(1, 17), 5))


def check(document, kind, domain=None):
    assert set(document) == {"variables", "constraints"}
    assert document["variables"] == [
        {"name": [f"block_{i}"], "domain": [0, 1]} for i in range(4368)
    ]
    rows = [(list(range(4368)), [64, 64])]
    if kind == "inversive-pool":
        assert len(domain) == len(set(map(tuple, domain))) == 288
        assert all(tuple(b) in BLOCKS for b in domain)
        allowed = set(map(tuple, domain))
        rows.extend(([i], [0, 0]) for i, b in enumerate(BLOCKS) if b not in allowed)
    for t in combinations(range(1, 17), 3):
        exact = kind == "paired-balanced" and len({(p + 1) // 2 for p in t}) == 3
        ids = [i for i, b in enumerate(BLOCKS) if set(t) <= set(b)]
        rows.append((ids, [1, 1 if exact else 9223372036854775807]))
    if kind == "paired-balanced":
        ids = [i for i, b in enumerate(BLOCKS) if len({(p + 1) // 2 for p in b}) == 4]
        rows.append((ids, [0, 0]))
    assert document["constraints"] == [
        {"linear": [{"vars": ids, "coeffs": [1] * len(ids), "domain": bounds}]}
        for ids, bounds in rows
    ]
    return {"variables": 4368, "constraints": len(rows), "valid": True}


def main():
    report = {"source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    for kind in ["paired-balanced", "inversive-pool"]:
        run = HERE / kind
        domain = json.loads((run / "domain.json").read_text()) if kind == "inversive-pool" else None
        source = (run / "model.pbtxt").read_bytes()
        metadata = json.loads((run / "result.json").read_text())
        assert hashlib.sha256(source).hexdigest() == metadata["model_sha256"]
        parsed = READER.parse_pbtxt(source.decode())
        result = check(parsed, kind, domain)
        result["model_sha256"] = metadata["model_sha256"]
        result["negative_controls"] = []
        for damage in ["coverage", "coefficient", "ordering"]:
            bad = copy.deepcopy(parsed)
            if damage == "coverage":
                bad["constraints"].pop()
            elif damage == "coefficient":
                bad["constraints"][0]["linear"][0]["coeffs"][0] = 2
            else:
                bad["variables"][0]["name"] = ["block_1"]
            try:
                check(bad, kind, domain)
            except AssertionError:
                result["negative_controls"].append(damage)
            else:
                raise AssertionError("accepted damaged model")
        report[kind] = result
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
