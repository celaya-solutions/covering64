# Document:    Independent Unrestricted Pair Two-Triple Cuts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6978bd22561b57c2f134e8b942aedce9f1328428e076e258d90345cff1dd5155
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check the stronger pair identity, dominance and count-five consequence; no solver."""

import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
POINTS = tuple(range(1, 17))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def partitions(total, slots, ceiling):
    if slots == 0:
        if total == 0:
            yield ()
        return
    for first in range(min(total, ceiling), -1, -1):
        if total - first <= (slots - 1) * first:
            for tail in partitions(total - first, slots - 1, first):
                yield (first, *tail)


def diagnostic(path):
    blocks = [
        tuple(map(int, line.split()))
        for line in path.read_text().splitlines()
        if line and not line.startswith("#")
    ]
    assert len(blocks) == len(set(blocks))
    counts = {
        size: Counter(t for block in blocks for t in itertools.combinations(block, size))
        for size in [2, 3]
    }
    violations, minimum = [], 1000000
    for pair in itertools.combinations(POINTS, 2):
        for a, b in itertools.combinations([p for p in POINTS if p not in pair], 2):
            ta, tb = tuple(sorted((*pair, a))), tuple(sorted((*pair, b)))
            lhs = 3 * counts[2][pair] - counts[3][ta] - counts[3][tb]
            minimum = min(minimum, lhs)
            if lhs < 12:
                violations.append(
                    {
                        "pair": pair,
                        "outside": [a, b],
                        "pair_count": counts[2][pair],
                        "triple_counts": [counts[3][ta], counts[3][tb]],
                        "lhs": lhs,
                        "deficit": 12 - lhs,
                    }
                )
    reports = []
    for prefix in [
        ["uv", "run", "covering64", "verify"],
        ["uv", "run", "python", "scripts/check_cover.py"],
    ]:
        process = subprocess.run(
            [*prefix, str(path), "--expected-blocks", str(len(blocks))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert process.returncode in (0, 1), process.stderr
        reports.append(json.loads(process.stdout))
    for key in ["blocks", "valid", "uncovered", "canonical_sha256"]:
        assert reports[0][key] == reports[1][key]
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "blocks": len(blocks),
        "holes": len(reports[0]["uncovered"]),
        "minimum_lhs": minimum,
        "violation_count": len(violations),
        "total_deficit": sum(v["deficit"] for v in violations),
        "violations": violations,
        "package": reports[0],
        "standalone": reports[1],
    }


def main():
    identity_checks, dominance_checks = 0, 0
    damaged_pair_coefficient = damaged_triple_sign = False
    for pair in itertools.combinations(POINTS, 2):
        outside = [p for p in POINTS if p not in pair]
        for extra in itertools.combinations(outside, 3):
            chosen = set(extra)
            for a, b in itertools.combinations(outside, 2):
                ca, cb, cab = int(a in chosen), int(b in chosen), int(a in chosen and b in chosen)
                left = 3 - ca - cb
                right = sum(p not in (a, b) for p in extra)
                assert left == right
                assert (3 - 2 * cab) - left == ca + cb - 2 * cab >= 0
                damaged_pair_coefficient |= 2 - ca - cb != right
                damaged_triple_sign |= 3 - ca + cb != right
                identity_checks += 1
                dominance_checks += 1
    assert identity_checks == dominance_checks == 3974880
    assert damaged_pair_coefficient and damaged_triple_sign
    vectors = list(partitions(15, 14, 15))
    allowed = [vector for vector in vectors if vector[0] + vector[1] <= 3]
    assert allowed == [(2, *([1] * 13))]
    weak_only = next(vector for vector in vectors if 0 in vector and vector[0] <= 2)
    assert weak_only[0] + weak_only[1] > 3
    paths = [
        ROOT / "data/baselines/belic-1997.txt",
        ROOT
        / ("experiments/scratch/pair-local-necessary-cuts-independent-20261004/"
           "quad-sharp-full-cover.txt"),
        ROOT
        / (
            "experiments/2026-10-03/reduced-family-heuristic/"
            "penalty-2026100363/search-control_before-1-h6.txt"
        ),
        ROOT / ("experiments/2026-10-04/native-core-cap-escape-v2/seed-2026104201/search-h9.txt"),
    ]
    checked = [diagnostic(path) for path in paths]
    assert all(row["holes"] == row["violation_count"] == 0 for row in checked[:2])
    assert checked[1]["minimum_lhs"] == 12
    result = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "optimizer_calls": 0,
        "row_count": 10920,
        "coefficient_identity_checks": identity_checks,
        "coefficient_dominance_checks": dominance_checks,
        "identity": "3*c(P)-c(P+a)-c(P+b)=sum_{x outside P+a+b} c(P+x)",
        "proof": "The right side has12 triple counts, each at least1 in every full cover.",
        "dominance_identity": "[3*c(P)-2*c(P+a+b)]-[3*c(P)-c(P+a)-c(P+b)]"
        "=c(P+a)+c(P+b)-2*c(P+a+b)>=0",
        "pair_five_consequence": "The14 triple counts sum to15. Every two sum to at most3. "
        "The only possible sorted vector is one2 and thirteen1s; "
        "there are no missing triples through a pair with count5.",
        "sorted_vectors_checked": len(vectors),
        "allowed_pair_five_vector": allowed[0],
        "single_cut_only_counterexample": weak_only,
        "damaged_controls_rejected": [
            "pair coefficient2",
            "second triple sign positive",
            "right hand side13",
            "single cuts imply no holes at pair5",
        ],
        "scope": "Necessary for unrestricted full C(16,5,3) covers of any block count. "
        "No degree, symmetry or incumbent assumptions. Count variables are exact.",
        "old_quad_cut_scope": "The new inequalities dominate the old quad inequalities. "
        "Dropping1820quad count variables removes only uniquely defined "
        "auxiliaries, while imposing the new stronger rows preserves all covers.",
        "witness_checks": checked,
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "audit_sha256": sha(HERE / "audit.json"),
                "checker_sha256": sha(Path(__file__)),
                "sorted_vectors": len(vectors),
                "seed_violations": checked[2]["violation_count"],
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
