# Document:    Independent Empty-Support Two-Swap Control
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b8114b155e8f3518ab0035b2a05555742221e39dd3f7c8c57cb57bff94fb5101
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One fixed real support-zero fixture; no search or full neighborhood scan."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-two-swap-scan-independent-20261004"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = RAW / "empty-support.json"
    assert not output.exists(), "preserve support-zero control"
    original = json.loads((RAW / "control-expectations.json").read_text())
    source = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    assert sha(source) == original["oracle_sha256"]
    spec = importlib.util.spec_from_file_location("empty_support_oracle", source)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    chosen = set(original["base_ids"])
    b, c, a = 1142, 1871, 145
    assert b in chosen and c in chosen and a not in chosen
    ids = sorted((chosen - {b, c}) | {a})
    partial = oracle.analyze(ids, original["core_rows"])
    assert min(partial["counts"][2]) == 5
    completions, checks = [], 0
    for d in range(a + 1, 4368):
        if d in chosen:
            continue
        block = oracle.MASKS[5][d]
        assert all(
            count + int(pair & block == pair) >= 5
            for pair, count in zip(oracle.MASKS[2], partial["counts"][2], strict=True)
        )
        completions.append(d)
        checks += 1
    case = {
        "outgoing": [b, c],
        "first_incoming": a,
        "pair_counts": partial["counts"][2],
        "worst_deficit": 0,
        "support_mask": 0,
        "category": "support_0",
        "expected_completions": completions,
        "partial": {"ids": ids, **partial},
    }
    final = []
    for d in (completions[0], completions[-1]):
        ids = sorted((chosen - {b, c}) | {a, d})
        final.append(
            {
                "outgoing": [b, c],
                "incoming": [a, d],
                "ids": ids,
                **oracle.analyze(ids, original["core_rows"]),
            }
        )
    record = {
        "source_sha256": sha(Path(__file__)),
        "oracle_sha256": sha(source),
        "base_sha256": original["base_sha256"],
        "fixtures": [case],
        "final_snapshots": final,
        "completion_checks": checks,
        "optimizer_launches": 0,
    }
    output.write_text(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "completion_checks": checks, "sha256": sha(output)}))


if __name__ == "__main__":
    main()
