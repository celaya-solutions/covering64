# Document:    Parametric Heavy-Block Inequality Derivation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2b83389a0d53f63a51b158a301df33782bc5ac4e7fa0e04e93159e70e9e65aec
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import itertools as it
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "lookahead-heavy-strengthened"
GATE = HERE.parent / "native-ten-hole-completion-independent"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    dual_path = SOURCE / "dual.json"
    dual = json.loads(dual_path.read_text())
    audit = json.loads((GATE / "dual-audit.json").read_text())
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    assert audit["passed"] and audit["dual_sha256"] == sha(dual_path)
    assert audit["checker_sha256"] == sha(GATE / "check_dual.py")
    assert audit["model_sha256"] == manifest["model_sha256"]
    assert sha(ROOT / manifest["model"]) == manifest["model_sha256"]
    universe = list(it.combinations(range(1, 17), 5))
    ids = {b: i for i, b in enumerate(universe)}
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    hubs = {4, 8, 12, 16}
    ordinary = [b for b in universe if all(len(set(b) & a) <= 1 for a in anchors)]
    heavy = [
        b
        for b in universe
        if any(a <= set(b) for a in anchors) and all(len(set(b) & a) in (0, 1, 3) for a in anchors)
    ]
    assert len(ordinary) == 1200 and len(heavy) == 276
    # Each row has constant bounds before subtracting its heavy-block incidence.
    rows = [((), 64, 64)]
    for triple in it.combinations(range(1, 17), 3):
        rows.append((triple, 1, None if set(triple) in anchors else 2))
    rows.extend(((p,), 20, 20) for p in range(1, 17))
    for pair in it.combinations(range(1, 17), 2):
        point = next((p for p in pair if p not in hubs), None)
        if point is None:
            lower, upper = 5, 7
        else:
            other = next(p for p in pair if p != point)
            group = anchors[(point - 1) // 4]
            lower = upper = 7 if other in group else 6 if other == max(group) + 1 else 5
        rows.append((pair, lower, upper))
    assert len(rows) == 697
    weights = dict(dual["weights"])
    assert len(weights) == len(dual["weights"])
    row_map = {
        "format": "v1.0.0",
        "ordinary_domain": [0, 1],
        "bound_formula": "constant_bound - sum(h_b for heavy blocks b containing subset)",
        "empty_subset": "contained in every block",
        "dual_sha256": sha(dual_path),
        "rows": [
            {
                "index": i,
                "kind": "cardinality"
                if i == 0
                else "triple"
                if i <= 560
                else "point"
                if i <= 576
                else "pair",
                "subset": list(subset),
                "lower": lower,
                "upper": upper,
                "weight": weights.get(i, 0),
            }
            for i, (subset, lower, upper) in enumerate(rows)
        ],
    }
    (HERE / "row-map.json").write_text(json.dumps(row_map, indent=2) + "\n")
    ordinary_coefficients, heavy_coefficients = [0] * 1200, [0] * 276
    constant = 0
    for index, weight in weights.items():
        subset, lower, upper = rows[index]
        bound = lower if weight > 0 else upper
        assert bound is not None
        constant += weight * bound
        for blocks, coefficients in [
            (ordinary, ordinary_coefficients),
            (heavy, heavy_coefficients),
        ]:
            for j, block in enumerate(blocks):
                if set(subset) <= set(block):
                    coefficients[j] += weight
    box = sum(max(0, c) for c in ordinary_coefficients)
    threshold = constant - box
    seed_path = HERE.parent / "lookahead-heavy-completion/seed.txt"
    seed = [tuple(map(int, line.split())) for line in seed_path.read_text().splitlines()]
    seed_heavy = set(seed) & set(heavy)
    assert len(seed_heavy) == 28
    score = sum(c for b, c in zip(heavy, heavy_coefficients, strict=True) if b in seed_heavy)
    assert constant - score == dual["rhs_numerator"]
    assert box == dual["box_max_numerator"]
    assert threshold - score > 0
    cut = {
        "version": "v1.0.0",
        "direction": ">=",
        "rhs": threshold,
        "heavy_global_ids": [ids[b] for b in heavy],
        "heavy_blocks": heavy,
        "coefficients": heavy_coefficients,
        "ordinary_global_ids": [ids[b] for b in ordinary],
        "ordinary_combined_coefficients": ordinary_coefficients,
        "constant_numerator": constant,
        "ordinary_box_max_numerator": box,
        "denominator": dual["denominator"],
        "dual_sha256": sha(dual_path),
        "source_model_sha256": manifest["model_sha256"],
        "source_gate_sha256": sha(GATE / "dual-audit.json"),
        "row_map_sha256": sha(HERE / "row-map.json"),
        "deriver_sha256": sha(Path(__file__)),
        "seed_sha256": sha(seed_path),
        "seed_heavy_global_ids": sorted(ids[b] for b in seed_heavy),
        "seed_lhs": score,
        "seed_violation_numerator": threshold - score,
        "scope": "Necessary inequality for regular degree20 four-sevenfold completions "
        "with these four anchor triples and their own hubs; all six hub graphs retained. "
        "Not an unrestricted covering bound or a first-link exclusion.",
    }
    (HERE / "cut.json").write_text(json.dumps(cut, indent=2) + "\n")
    print(
        json.dumps(
            {
                "heavy_coefficients": len(heavy_coefficients),
                "rhs": threshold,
                "seed_lhs": score,
                "violation_numerator": threshold - score,
                "denominator": dual["denominator"],
                "cut_sha256": sha(HERE / "cut.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
