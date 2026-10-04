# Document:    Three-Deletion Upper Screen Independent Data Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e55bfc388a858c64913f83d93f1de555b6659f7443c88b44d4591470e96c206e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Direct owner-mask recount; all survivors plus a deterministic excluded sample."""

import csv
import hashlib
import itertools
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNS_SHA = "1037a8f8a33aa89585800dfffc784815db06f7c1b6d92e3e53d3aff708b74a54"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert sha(HERE / "runs.json") == RUNS_SHA
    producer = json.loads((HERE / "runs.json").read_text())
    for kind in ("source", "binary", "compiler_version"):
        assert sha(ROOT / producer[f"{kind}_path"]) == producer[f"{kind}_sha256"]
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    ranks = {block: index for index, block in enumerate(blocks)}
    triple_ranks = {triple: index for index, triple in enumerate(triples)}
    masks = [sum(1 << triple_ranks[t] for t in itertools.combinations(b, 3)) for b in blocks]
    summaries = []
    for run in producer["runs"]:
        assert sha(ROOT / run["input_path"]) == run["input_sha256"]
        for relative, digest in run["raw_files"].items():
            assert sha(ROOT / relative) == digest
        family = [
            tuple(map(int, line.split()))
            for line in (ROOT / run["input_path"]).read_text().splitlines()
        ]
        assert len(family) == len(set(family)) == 64
        selected = [ranks[b] for b in family]
        assert selected == sorted(selected)
        positions = {block: index for index, block in enumerate(selected)}
        eligible = sorted(set(range(len(blocks))) - set(selected))
        owners = [0] * 560
        for index, block in enumerate(family):
            for triple in itertools.combinations(block, 3):
                owners[triple_ranks[triple]] |= 1 << index
        holes_mask = sum(1 << t for t, owner in enumerate(owners) if not owner)
        assert holes_mask.bit_count() == run["initial_holes"]
        owned = [(1 << t, owner) for t, owner in enumerate(owners) if owner]
        table_path = ROOT / next(p for p in run["raw_files"] if p.endswith("-deletions.tsv"))
        rows = list(csv.DictReader(table_path.open(), delimiter="\t"))
        assert len(rows) == math.comb(64, 3)
        expected_drops = itertools.combinations(selected, 3)
        direct_score_rows = 0
        histogram = Counter()
        survivor_tuple_upper = 0
        excluded_sample = 0
        survivors = 0
        for index, (row, expected) in enumerate(zip(rows, expected_drops, strict=True)):
            values = {k: int(v) for k, v in row.items()}
            dropped = tuple(values[f"delete{i}"] for i in range(3))
            assert dropped == expected
            deletion_mask = sum(1 << positions[block] for block in dropped)
            u = holes_mask
            for bit, owner in owned:
                if owner & ~deletion_mask == 0:
                    u |= bit
            missing = u.bit_count()
            demand = missing - run["target_holes"]
            assert missing == values["uncovered"] and demand == values["demand"]
            survives = not values["excluded"]
            if survives:
                survivors += 1
                histogram[values["adders_meeting_floor"]] += 1
                survivor_tuple_upper += math.comb(values["adders_meeting_floor"], 3)
            # All surviving rows; every1301st row samples excluded cases deterministically.
            sampled = bool(values["excluded"] and index % 1301 == 0)
            if not (survives or sampled):
                continue
            direct_score_rows += 1
            excluded_sample += sampled
            scores = [(masks[block] & u).bit_count() for block in eligible]
            top = sorted(scores, reverse=True)[:3]
            upper = sum(top)
            floor = max(0, demand - sum(top[:2]))
            assert top == [values[f"top{i}"] for i in range(3)]
            assert upper == values["upper"] and int(upper < demand) == values["excluded"]
            assert floor == values["adder_floor"]
            assert sum(value >= floor for value in scores) == values["adders_meeting_floor"]
        summaries.append(
            {
                "name": run["name"],
                "deletion_rows_recounted": len(rows),
                "direct_adder_score_rows": direct_score_rows,
                "all_survivors_directly_recounted": survivors,
                "excluded_rows_directly_sampled": excluded_sample,
                "surviving_deletions": survivors,
                "excluded_deletions": len(rows) - survivors,
                "survivor_pool_histogram": dict(sorted(histogram.items())),
                "necessary_addition_triples": survivor_tuple_upper,
            }
        )
    result = {
        "passed": True,
        "runs_sha256": RUNS_SHA,
        "checker_sha256": sha(__file__),
        "runs": summaries,
        "scope": "All deletion triples and uncovered counts independently recounted. "
        "All survivor rows and a deterministic excluded sample have direct full-universe "
        "adder scores checked. Not an independent recount of every excluded top-count. "
        "No replacement tuple search and no optimizer run.",
    }
    (HERE / "replay.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
