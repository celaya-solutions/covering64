# Document:    Complete Template Native Best-State Diagnostics
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      928a05be6d74d950863590e878daec823ca2e66754a153c13c786e1165c0c9a5
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Recount pair-target defects, nonheavy repetitions and acceptance by move type."""

import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-native-v1.0.0/pilots"


def targets(name):
    if name not in ["matching", "cycle"]:
        raise ValueError("unknown case")
    result = {p: 5 for p in it.combinations(range(1, 17), 2)}
    for group in range(4):
        anchor = range(4 * group + 1, 4 * group + 4)
        for pair in it.combinations(anchor, 2):
            result[pair] = 7
        for point in anchor:
            result[(point, 4 * group + 4)] = 6
    edges = [(4, 8), (12, 16)] if name == "matching" else [(4, 8), (8, 12), (12, 16), (4, 16)]
    for edge in edges:
        result[edge] += 2 if name == "matching" else 1
    return result


def main():
    heavy = {tuple(range(4 * g + 1, 4 * g + 4)) for g in range(4)}
    audit = json.loads((HERE / "pilot-audit.json").read_text())
    records = []
    for result in json.loads((HERE / "results.json").read_text()):
        name = result["name"]
        path = RAW / f"{name}-best.txt"
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        pairs = Counter(p for b in blocks for p in it.combinations(b, 2))
        triples = Counter(t for b in blocks for t in it.combinations(b, 3))
        checked = next(r for r in audit["snapshots"] if r["path"].endswith(f"/{name}-best.txt"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert checked["sha256"] == result["best_sha256"] == digest
        assert checked["pair_counts_lexicographic"] == [pairs[p] for p in targets(name)]
        native = result["native_result"]
        assert checked["holes"] == native["best_holes"]
        modes = ["directed_swap", "redistribution", "point_cycle", "template_replace"]
        rates = [
            {"mode": mode, "attempted": a, "accepted": b, "accepted_fraction": b / a if a else None}
            for mode, a, b in zip(
                modes,
                native.get("attempted", [0] * 4),
                native.get("accepted", [0] * 4),
                strict=True,
            )
        ]
        records.append(
            {
                "name": name,
                "best_sha256": digest,
                "best_holes": checked["holes"],
                "pair_target_l1": sum(
                    abs(pairs[p] - target) for p, target in targets(name).items()
                ),
                "pair_targets_lexicographic": list(targets(name).values()),
                "max_nonheavy_triple_multiplicity": max(
                    triples[t] for t in it.combinations(range(1, 17), 3) if t not in heavy
                ),
                "nonheavy_triples_above2": sum(
                    triples[t] > 2 for t in it.combinations(range(1, 17), 3) if t not in heavy
                ),
                "main_loop_mode_acceptance": rates,
                "rate_scope": (
                    "All main-loop proposals include invalid proposals; restarts separate."
                ),
            }
        )
    report = {
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": records,
        "scope": "Exact diagnostics; no score or restriction changed.",
    }
    (HERE / "diagnostics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            [
                {
                    k: r[k]
                    for k in [
                        "name",
                        "best_holes",
                        "pair_target_l1",
                        "max_nonheavy_triple_multiplicity",
                    ]
                }
                for r in records
            ]
        )
    )


if __name__ == "__main__":
    main()
