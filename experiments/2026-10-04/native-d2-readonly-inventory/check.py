# Document:    Independent D2max and D2sum Recount of Saved Native States
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      a310a2b2122dd63789ea59a4ad7d194ea034997205336979c82f1a3d39147c7a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Direct subset recount only; no producer metric imports or optimizer calls."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
NATIVE_AUDIT = DAY / "native-pair-penalty-independent/postcheck.json"
FIXTURES = [
    (
        "H6",
        "experiments/2026-10-03/reduced-family-heuristic/penalty-2026100363/"
        "search-control_before-1-h6.txt",
        "797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de",
        6,
    ),
    (
        "H48",
        "experiments/2026-10-04/native-pair-penalty/seed-2026104401/search-final-qualified.txt",
        "630461e4c8805916ac515114b308d6ed05b2a43da16605ea452150d7e3a784d3",
        48,
    ),
    (
        "H49",
        "experiments/2026-10-04/native-pair-penalty/seed-2026104402/search-final-qualified.txt",
        "a7feb783eb9f36e710feba5356857514cde146104b95de03fa47716126afd9c4",
        49,
    ),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound_witnesses(value):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            yield value["path"], value["sha256"]
        for child in value.values():
            yield from bound_witnesses(child)
    elif isinstance(value, list):
        for child in value:
            yield from bound_witnesses(child)


def recount(name, path, checksum, expected_holes):
    assert sha(path) == checksum
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64
    assert all(
        len(block) == len(set(block)) == 5
        and tuple(sorted(block)) == block
        and all(1 <= point <= 16 for point in block)
        for block in blocks
    )
    counts = {
        size: Counter(subset for block in blocks for subset in itertools.combinations(block, size))
        for size in (2, 3, 4)
    }
    holes = sum(counts[3][triple] == 0 for triple in itertools.combinations(range(1, 17), 3))
    assert holes == expected_holes
    per_pair = []
    d3 = d4 = 0
    for pair in itertools.combinations(range(1, 17), 2):
        outside = [point for point in range(1, 17) if point not in pair]
        position_counts = [(point, counts[3][tuple(sorted((*pair, point)))]) for point in outside]
        assert len(position_counts) == len({point for point, _ in position_counts}) == 14
        assert sum(count for _, count in position_counts) == 3 * counts[2][pair]
        top_two = sorted(position_counts, key=lambda item: (-item[1], item[0]))[:2]
        maximum = max(0, 12 - 3 * counts[2][pair] + sum(count for _, count in top_two))
        deficits, violations = [], []
        for (a, first), (b, second) in itertools.combinations(position_counts, 2):
            deficit = max(0, 12 - 3 * counts[2][pair] + first + second)
            deficits.append(deficit)
            if deficit:
                violations.append(
                    {"outside": [a, b], "triple_counts": [first, second], "deficit": deficit}
                )
            quad = tuple(sorted((*pair, a, b)))
            d4 += max(0, 12 - 3 * counts[2][pair] + 2 * counts[4][quad])
        d3 += sum(max(0, 13 - 3 * counts[2][pair] + count) for _, count in position_counts)
        assert len(deficits) == 91 and max(deficits) == maximum
        per_pair.append(
            {
                "pair": pair,
                "pair_count": counts[2][pair],
                "triple_position_counts": [
                    {"outside": point, "count": count} for point, count in position_counts
                ],
                "top_two_distinct_positions": [
                    {"outside": point, "count": count} for point, count in top_two
                ],
                "D2max_contribution": maximum,
                "D2sum_contribution": sum(deficits),
                "violating_rows": len(violations),
                "deficit_histogram": dict(sorted(Counter(deficits).items())),
                "violations": violations,
            }
        )
    assert len(per_pair) == 120
    assert (d3, d4) == ((4, 0) if name == "H6" else (0, 0))
    return {
        "name": name,
        "path": str(path.relative_to(ROOT)),
        "sha256": checksum,
        "holes": holes,
        "blocks": len(blocks),
        "D3": d3,
        "D4": d4,
        "minimum_pair_count": min(row["pair_count"] for row in per_pair),
        "D2max": sum(row["D2max_contribution"] for row in per_pair),
        "D2sum": sum(row["D2sum_contribution"] for row in per_pair),
        "violating_pairs": sum(row["D2max_contribution"] > 0 for row in per_pair),
        "violating_rows": sum(row["violating_rows"] for row in per_pair),
        "rows_checked": 10920,
        "per_pair": per_pair,
    }


def main():
    output = HERE / "result.json"
    assert not output.exists()
    assert sha(NATIVE_AUDIT) == "7c58bbd14d7a07dafd92fa776e23adcc7d24cd1d2c622755da8c6b7454c8ca32"
    audit = json.loads(NATIVE_AUDIT.read_text())
    assert audit["passed"] and not audit["cover_found"]
    bindings = list(bound_witnesses(audit))
    rows = []
    for name, relative, checksum, expected_holes in FIXTURES:
        assert any(bound_sha == checksum for _, bound_sha in bindings)
        rows.append(recount(name, ROOT / relative, checksum, expected_holes))
    result = {
        "passed": True,
        "optimizer_calls": 0,
        "source_sha256": sha(Path(__file__)),
        "verification_audit_path": str(NATIVE_AUDIT.relative_to(ROOT)),
        "verification_audit_sha256": sha(NATIVE_AUDIT),
        "records": rows,
        "definition_D2max": "sum_P max(0,12-3*c(P)+top1(P)+top2(P)); top positions are distinct",
        "definition_D2sum": "sum_P sum_{a<b outside P} max(0,12-3*c(P)+c(P+a)+c(P+b))",
        "scope": "Independent direct subset recount of three fixed, previously double-verified "
        "64-block states. Ties retain distinct triple positions. No native metric imports, "
        "model changes, implementation changes, or optimizer calls.",
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "result_sha256": sha(output),
                "records": [
                    {
                        key: row[key]
                        for key in [
                            "name",
                            "holes",
                            "D3",
                            "D4",
                            "D2max",
                            "D2sum",
                            "violating_pairs",
                            "violating_rows",
                        ]
                    }
                    for row in rows
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
