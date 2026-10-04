# Document:    Independent Unrestricted Pair Local Necessary Cuts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      36045e793901293269692bd0b404c0037f8fd9e5f549c7fb54c35e9bf7e04b37
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check exact counting identities, benchmark cuts and damaged controls; no solver."""

import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/pair-local-necessary-cuts-independent-20261004"
POINTS = tuple(range(1, 17))
BLOCKS = list(itertools.combinations(POINTS, 5))
TRIPLES = list(itertools.combinations(POINTS, 3))
QUADS = list(itertools.combinations(POINTS, 4))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    rows = [
        tuple(sorted(map(int, line.split())))
        for line in path.read_text().splitlines()
        if line and not line.startswith("#")
    ]
    assert len(rows) == len(set(rows))
    assert all(len(row) == len(set(row)) == 5 and set(row) <= set(POINTS) for row in rows)
    return rows


def verify(path):
    blocks = load(path)
    reports = []
    for command in [
        ["uv", "run", "covering64", "verify"],
        ["uv", "run", "python", "scripts/check_cover.py"],
    ]:
        process = subprocess.run(
            [*command, str(path), "--expected-blocks", str(len(blocks))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert process.returncode in (0, 1), process.stderr
        reports.append(json.loads(process.stdout))
    assert reports[0]["uncovered"] == reports[1]["uncovered"]
    assert reports[0]["valid"] == reports[1]["valid"]
    assert reports[0]["canonical_sha256"] == reports[1]["canonical_sha256"]
    assert reports[0]["blocks"] == reports[1]["blocks"] == len(blocks)
    counts = {
        k: Counter(item for block in blocks for item in itertools.combinations(block, k))
        for k in [2, 3, 4]
    }
    triple_rows, quad_rows = [], []
    for big, rows, weight, lower in [(TRIPLES, triple_rows, 1, 13), (QUADS, quad_rows, 2, 12)]:
        for superset in big:
            for pair in itertools.combinations(superset, 2):
                left = 3 * counts[2][pair] - weight * counts[len(superset)][superset]
                rows.append(
                    {
                        "pair": list(pair),
                        "superset": list(superset),
                        "pair_count": counts[2][pair],
                        "superset_count": counts[len(superset)][superset],
                        "lhs": left,
                        "rhs": lower,
                        "violated": left < lower,
                    }
                )
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "blocks": len(blocks),
        "holes": len(reports[0]["uncovered"]),
        "package": reports[0],
        "standalone": reports[1],
        "triple_row_count": len(triple_rows),
        "quad_row_count": len(quad_rows),
        "minimum_triple_lhs": min(row["lhs"] for row in triple_rows),
        "minimum_quad_lhs": min(row["lhs"] for row in quad_rows),
        "triple_violations": [row for row in triple_rows if row["violated"]],
        "quad_violations": [row for row in quad_rows if row["violated"]],
    }


def main():
    triple_checks = quad_checks = 0
    coefficient_mutants = [False, False]
    for pair in itertools.combinations(POINTS, 2):
        outside = tuple(p for p in POINTS if p not in pair)
        # Columns not containing P contribute zero to both sides by subset inclusion.
        for extra in itertools.combinations(outside, 3):
            chosen = set(extra)
            for a in outside:
                lhs = 3 - (a in chosen)
                rhs = sum(x in chosen for x in outside if x != a)
                assert lhs == rhs
                coefficient_mutants[0] |= 2 - (a in chosen) != rhs
                triple_checks += 1
            for a, b in itertools.combinations(outside, 2):
                both = a in chosen and b in chosen
                lhs = 3 - 2 * both
                residual_a = int(a in chosen) - int(both)
                residual_b = int(b in chosen) - int(both)
                assert residual_a >= 0 and residual_b >= 0
                rhs = sum(x not in (a, b) for x in extra) + residual_a + residual_b
                assert lhs == rhs
                coefficient_mutants[1] |= 3 - both != rhs
                quad_checks += 1
    assert triple_checks == 611520 and quad_checks == 3974880
    assert all(coefficient_mutants)
    RAW.mkdir(parents=True, exist_ok=True)
    # A full, deliberately unbalanced control makes the quadruple constant12 sharp.
    pair = {1, 2}
    control = [block for block in BLOCKS if not pair <= set(block)]
    control += [
        (1, 2, *extra)
        for extra in [(3, 4, 5), (3, 4, 6), (3, 4, 7), (8, 9, 10), (11, 12, 13), (14, 15, 16)]
    ]
    control_path = RAW / "quad-sharp-full-cover.txt"
    control_path.write_text("".join(" ".join(map(str, row)) + "\n" for row in sorted(control)))
    paths = [
        ROOT / "data/baselines/belic-1997.txt",
        control_path,
        ROOT
        / (
            "experiments/2026-10-03/reduced-family-heuristic/"
            "penalty-2026100363/search-control_before-1-h6.txt"
        ),
        ROOT / ("experiments/2026-10-04/native-core-cap-escape-v2/seed-2026104201/search-h9.txt"),
    ]
    checked = [verify(path) for path in paths]
    for row in checked[:2]:
        assert row["holes"] == 0 and not row["triple_violations"] and not row["quad_violations"]
    assert checked[0]["blocks"] == 65 and checked[0]["minimum_triple_lhs"] == 13
    assert checked[1]["blocks"] == 4010 and checked[1]["minimum_quad_lhs"] == 12
    assert checked[2]["holes"] == 6 and len(checked[2]["triple_violations"]) == 4
    assert not checked[2]["quad_violations"]
    assert checked[3]["holes"] == 9
    result = {
        "passed": True,
        "check_sha256": sha(Path(__file__)),
        "optimizer_calls": 0,
        "parameters": {"v": 16, "k": 5, "t": 3},
        "triple_cut_rows": 1680,
        "quadruple_cut_rows": 10920,
        "carrier_triple_coefficient_checks": triple_checks,
        "carrier_quadruple_coefficient_checks": quad_checks,
        "noncarrier_columns": "All terms are zero since every counted superset contains P.",
        "identities": [
            "3*c(P)-c(P+a)=sum_{x outside P+a} c(P+x)",
            "3*c(P)-2*c(P+a+b)=sum_{x outside P+a+b}c(P+x)+[c(P+a)-c(P+a+b)]+[c(P+b)-c(P+a+b)]",
        ],
        "proof": "In a full cover every triple count is at least1. "
        "The two bracketed differences are nonnegative by containment. "
        "There are13 and12 terms respectively in the sums.",
        "scope": "Necessary for every full C(16,5,3) cover, any block count or degrees. "
        "No symmetry, regularity, incumbent or rotational assumption.",
        "implied_by_complete_coverage_constraints": True,
        "use_in_partial_construction": "They exclude partial states even when hole variables "
        "allow missing triples; this is valid only as a target-cover restriction.",
        "damaged_controls_rejected": [
            "triple pair coefficient2",
            "quad repetition coefficient1",
            "triple rhs14",
            "quad rhs13",
        ],
        "sharp_control_scope": "The4010-block cover tests the unrestricted inequality constant; "
        "it is not a64-block candidate or a new upper bound.",
        "prior_local_derivations": {
            "path": "experiments/2026-10-03/regular-heavy-hub-bound/README.md",
            "sha256": sha(ROOT / "experiments/2026-10-03/regular-heavy-hub-bound/README.md"),
            "triple_line": 20,
            "quadruple_line": 26,
            "interpretation": "The local counting already appears there; later hub conclusions "
            "use degree20. No general all-pair row implementation was found "
            "in the targeted indexed-source and Markdown searches.",
        },
        "witness_checks": checked,
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "audit_sha256": sha(HERE / "audit.json"),
                "coefficient_checks": triple_checks + quad_checks,
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
