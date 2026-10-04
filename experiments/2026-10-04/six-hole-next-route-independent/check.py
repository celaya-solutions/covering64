# Document:    Independent Six Hole Single Exchange Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exhaust the declared one-block neighborhoods using triple-bit incidence."""

import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "six-hole-next-route/assessment.json"
BLOCKS = list(combinations(range(1, 17), 5))
TRIPLES = list(combinations(range(1, 17), 3))
RANK = {b: i for i, b in enumerate(BLOCKS)}
TRANK = {t: i for i, t in enumerate(TRIPLES)}
SUPPORT = [[TRANK[t] for t in combinations(b, 3)] for b in BLOCKS]
BITS = [sum(1 << t for t in row) for row in SUPPORT]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source = json.loads(SOURCE.read_text())
    for path, digest in source["input_files"].items():
        assert sha(ROOT / path) == digest
    reports = []
    for state in source["states"]:
        path = ROOT / state["path"]
        assert sha(path) == state["sha256"]
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()
                  if line and not line.startswith("#")]
        selected = {RANK[b] for b in blocks}
        assert len(selected) == len(blocks) == 64
        counts = Counter(t for i in selected for t in SUPPORT[i])
        holes = {t for t in range(560) if counts[t] == 0}
        assert len(holes) == 6
        missing = sum(1 << t for t in holes)
        additions = sorted(set(range(4368)) - selected)
        histogram, raw, eligible = Counter(), [], []
        for remove in sorted(selected):
            lost = {t for t in SUPPORT[remove] if counts[t] == 1}
            missing_after = missing | sum(1 << t for t in lost)
            uncovered_after = 6 + len(lost)
            for add in additions:
                objective = uncovered_after - (missing_after & BITS[add]).bit_count()
                histogram[objective] += 1
                if objective >= 6:
                    continue
                raw.append({"remove_global_id": remove, "add_global_id": add,
                            "holes": objective})
                adjusted = counts.copy()
                adjusted.subtract(SUPPORT[remove])
                adjusted.update(SUPPORT[add])
                assert sum(adjusted[t] == 0 for t in range(560)) == objective
                heavy = [t for t in range(560) if adjusted[t] >= 6]
                forbidden = any(
                    len({p for t in five for p in TRIPLES[t]}) == 15
                    and sum(adjusted[t] >= 7 for t in five) >= 2
                    for five in combinations(heavy, 5)
                )
                if not forbidden:
                    eligible.append(raw[-1])
        expected = state["exchanges"]
        assert sum(histogram.values()) == expected["directed_distinct_exchanges"] == 275456
        assert [list(x) for x in sorted(histogram.items())] == expected["hole_count_histogram"]
        assert raw == expected["strict_improvements"]
        assert len(raw) == expected["strict_improvement_count"]
        assert len(eligible) == expected["eligible_strict_improvement_count"] == 0
        reports.append({"path": state["path"], "sha256": state["sha256"],
                        "exchanges": sum(histogram.values()), "raw_improvements": len(raw),
                        "profile_eligible_improvements": len(eligible)})
    report = {"passed": True, "optimizer_calls": 0, "source_sha256": sha(__file__),
              "assessment_sha256": sha(SOURCE), "states": reports,
              "exchanges": sum(r["exchanges"] for r in reports),
              "raw_improvements": sum(r["raw_improvements"] for r in reports),
              "scope": "Only the complete one-block neighborhoods of these four saved states."}
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
