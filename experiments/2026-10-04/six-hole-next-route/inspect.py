# Document:    Six-Hole Adaptive Pool and Single-Exchange Assessment
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4ee25453941c53dd61fbc35c7f9bf81f3a14bd8921453c963f16ad9f62cdbd99
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Count deterministic adaptive pools and one-exchange moves without a solver."""

import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
BLOCKS = list(combinations(range(1, 17), 5))
TRIPLES = list(combinations(range(1, 17), 3))
BLOCK_ID = {block: i for i, block in enumerate(BLOCKS)}
TRIPLE_ID = {triple: i for i, triple in enumerate(TRIPLES)}
COVERS = [[TRIPLE_ID[t] for t in combinations(block, 3)] for block in BLOCKS]
MASKS = [sum(1 << i for i in row) for row in COVERS]
POINT_MASKS = [sum(1 << p for p in triple) for triple in TRIPLES]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def forbidden(counts):
    heavy = [i for i, n in enumerate(counts) if n >= 6]
    return any(
        sum(counts[i] >= 7 for i in family) >= 2
        and (sum(POINT_MASKS[i] for i in family).bit_count() == 15)
        and len(set().union(*(set(TRIPLES[i]) for i in family))) == 15
        for family in combinations(heavy, 5)
    )


def exchange_counts(ids):
    selected = set(ids)
    counts = [0] * len(TRIPLES)
    for i in ids:
        for t in COVERS[i]:
            counts[t] += 1
    holes = sum(1 << i for i, n in enumerate(counts) if n == 0)
    assert holes.bit_count() == 6 and not forbidden(counts)
    incoming = [i for i in range(len(BLOCKS)) if i not in selected]
    histogram, eligible_histogram = Counter(), Counter()
    strict, eligible = [], []
    for out in ids:
        private = sum(1 << i for i in COVERS[out] if counts[i] == 1)
        needed = holes | private
        for into in incoming:
            remaining = (needed & ~MASKS[into]).bit_count()
            histogram[remaining] += 1
            if remaining >= 6:
                continue
            changed = counts.copy()
            for i in COVERS[out]:
                changed[i] -= 1
            for i in COVERS[into]:
                changed[i] += 1
            assert sum(n == 0 for n in changed) == remaining
            entry = {"remove_global_id": out, "add_global_id": into, "holes": remaining}
            strict.append(entry)
            if not forbidden(changed):
                eligible_histogram[remaining] += 1
                eligible.append(entry)
    return {
        "directed_distinct_exchanges": len(ids) * len(incoming),
        "hole_count_histogram": sorted(histogram.items()),
        "strict_improvement_count": len(strict),
        "eligible_strict_improvement_count": len(eligible),
        "eligible_strict_improvement_histogram": sorted(eligible_histogram.items()),
        "best_raw_holes": min(histogram),
        "best_eligible_strict_holes": min(eligible_histogram) if eligible_histogram else None,
        "strict_improvements": strict,
    }


def main():
    audit_path = DAY / "heterogeneous-profile-postcheck/audit.json"
    manifest_path = DAY / "heterogeneous-profile-pool/manifest.json"
    audit = json.loads(audit_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    assert audit["passed"] and audit["producer_manifest_sha256"] == sha(manifest_path)
    states = [row for row in audit["checked_states"] if row["facts"]["holes"] == 6]
    assert len(states) == 4
    union, holes, records = set(), set(), []
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), audit_path, manifest_path]}
    for state in states:
        path = ROOT / state["path"]
        assert sha(path) == state["sha256"]
        inputs[state["path"]] = state["sha256"]
        blocks = [
            tuple(map(int, line.split()))
            for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        assert len(blocks) == len(set(blocks)) == 64
        assert all(block in BLOCK_ID for block in blocks)
        ids = sorted(BLOCK_ID[b] for b in blocks)
        union.update(ids)
        holes.update(tuple(t) for t in state["facts"]["missing_triples"])
        records.append(
            {"path": state["path"], "sha256": state["sha256"], "exchanges": exchange_counts(ids)}
        )
    carriers = {
        i for i, block in enumerate(BLOCKS) if any(set(triple) <= set(block) for triple in holes)
    }
    swaps = {
        BLOCK_ID[tuple(sorted(set(BLOCKS[i]) - {p} | {q}))]
        for i in union
        for p in BLOCKS[i]
        for q in range(1, 17)
        if q not in BLOCKS[i]
    }
    old = set(manifest["cases"][0]["pool"])
    assert len(old) == 277
    report = {
        "source_sha256": sha(__file__),
        "input_files": inputs,
        "optimizer_calls": 0,
        "four_state_union": len(union),
        "distinct_missing_triples": sorted(holes),
        "all_hole_carriers": len(carriers),
        "all_one_point_swaps": len(swaps),
        "union_plus_carriers": len(union | carriers),
        "union_plus_carriers_plus_swaps": len(union | carriers | swaps),
        "prior_elite_plus_carriers": len(old | carriers),
        "prior_elite_plus_carriers_plus_swaps": len(old | carriers | swaps),
        "adaptive_pool_global_ids": sorted(old | carriers),
        "states": records,
        "scope": "Finite pool and one-exchange enumeration of four saved states; no optimizer.",
    }
    (HERE / "assessment.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ["input_files", "states", "adaptive_pool_global_ids"]
            }
        )
    )
    for row in records:
        print(
            json.dumps(
                {
                    "path": row["path"],
                    **{k: v for k, v in row["exchanges"].items() if k != "strict_improvements"},
                }
            )
        )


if __name__ == "__main__":
    main()
