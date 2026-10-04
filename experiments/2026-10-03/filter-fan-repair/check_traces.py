# Document:    Independent Filter-and-Fan Prefix and Rollback Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      26112d2fa180d2a7070c4444960e13f7d5545f50deb2d9f5e664cf540789540f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reconstruct all coverage and degree counts from lexicographic block IDs."""

import argparse
import copy
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

BLOCKS = list(combinations(range(1, 17), 5))
TRIPLES = list(combinations(range(1, 17), 3))
TRIPLE_IDS = {triple: index for index, triple in enumerate(TRIPLES)}
INCIDENCE = [tuple(TRIPLE_IDS[t] for t in combinations(b, 3)) for b in BLOCKS]


def require(value, message):
    if not value:
        raise ValueError(message)


def recount(ids):
    require(len(ids) == len(set(ids)) == 64, "distinct cardinality")
    require(all(type(i) is int and 0 <= i < 4368 for i in ids), "block ID range")
    counter = Counter(t for i in ids for t in INCIDENCE[i])
    counts = [counter[t] for t in range(560)]
    degrees = [sum(p in BLOCKS[i] for i in ids) for p in range(1, 17)]
    require(sum(counts) == 640 and sum(degrees) == 320, "incidence totals")
    return counts, degrees


def inspect(record):
    require(set(record) == {"kind", "start_ids", "weights", "moves", "end_ids", "end_counts",
                            "deficit", "rollback_exact"}, "trace fields")
    require(record["kind"] in {"prefix-control", "explored", "improvement", "greedy-component"},
            "trace kind")
    require(type(record["deficit"]) is int and len(record["end_counts"]) == 560 and
            all(type(x) is int and x >= 0 for x in record["end_counts"]), "saved count types")
    ids = record["start_ids"].copy()
    start_counts, start_degrees = recount(ids)
    weights = record["weights"]
    require(len(weights) == 560 and all(type(w) is int and w > 0 for w in weights), "weights")
    degree_changes = 0
    for move in record["moves"]:
        require(set(move) == {"slot", "old", "incoming", "before", "after",
                              "energy_before", "energy_after"}, "move fields")
        require(all(type(value) is int for value in move.values()), "move integer fields")
        slot, old, incoming = (move[key] for key in ("slot", "old", "incoming"))
        require(type(slot) is int and 0 <= slot < 64 and ids[slot] == old, "stale move")
        require(type(incoming) is int and 0 <= incoming < 4368 and incoming not in ids,
                "invalid incoming block")
        counts, degrees = recount(ids)
        require(move["before"] == counts.count(0) and move["energy_before"] ==
                sum(w for w, c in zip(weights, counts, strict=True) if c == 0), "before score")
        ids[slot] = incoming
        counts, next_degrees = recount(ids)
        degree_changes += degrees != next_degrees
        require(move["after"] == counts.count(0) and move["energy_after"] ==
                sum(w for w, c in zip(weights, counts, strict=True) if c == 0), "after score")
    counts, _ = recount(ids)
    require(ids == record["end_ids"] and counts == record["end_counts"] and
            counts.count(0) == record["deficit"], "saved final state")
    if record["kind"] == "improvement":
        require(counts.count(0) < start_counts.count(0), "not a strict improvement")
    for move in reversed(record["moves"]):
        require(ids[move["slot"]] == move["incoming"] and move["old"] not in ids,
                "invalid inverse")
        ids[move["slot"]] = move["old"]
        recount(ids)
    counts, degrees = recount(ids)
    require(record["rollback_exact"] is True and ids == record["start_ids"] and
            counts == start_counts and degrees == start_degrees, "rollback")
    return len(record["moves"]), degree_changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked, moves, changed_degrees, sample = 0, 0, 0, None
    hashes = {}
    for path in args.paths:
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        for line in path.read_text().splitlines():
            record = json.loads(line)
            n, degrees = inspect(record)
            checked += 1
            moves += n
            changed_degrees += degrees
            if sample is None and record["moves"]:
                sample = record
    require(sample is not None, "no replayable moves")
    controls = []
    for label in ("duplicate seed", "wrong outgoing", "duplicate incoming", "bad slot",
                  "wrong before", "wrong after", "wrong weighted score", "damaged count",
                  "damaged final IDs", "false rollback", "bad weight", "out of range ID",
                  "boolean move", "bad kind"):
        bad = copy.deepcopy(sample)
        move = bad["moves"][0]
        if label == "duplicate seed":
            bad["start_ids"][1] = bad["start_ids"][0]
        elif label == "wrong outgoing":
            move["old"] = -1
        elif label == "duplicate incoming":
            move["incoming"] = bad["start_ids"][(move["slot"] + 1) % 64]
        elif label == "bad slot":
            move["slot"] = 64
        elif label == "wrong before":
            move["before"] += 1
        elif label == "wrong after":
            move["after"] += 1
        elif label == "wrong weighted score":
            move["energy_after"] += 1
        elif label == "damaged count":
            bad["end_counts"][0] += 1
        elif label == "damaged final IDs":
            bad["end_ids"][0] = -1
        elif label == "false rollback":
            bad["rollback_exact"] = False
        elif label == "bad weight":
            bad["weights"][0] = 0
        elif label == "out of range ID":
            move["incoming"] = 4368
        elif label == "boolean move":
            move["before"] = bool(move["before"])
        else:
            bad["kind"] = "unrecognized"
        try:
            inspect(bad)
        except ValueError:
            controls.append(dict(mutation=label, rejected=True))
        else:
            raise ValueError("damaged trace accepted: " + label)
    result = dict(passed=True, traces=checked, replayed_moves=moves,
                  moves_changing_point_degrees=changed_degrees, damaged_controls=controls,
                  input_sha256=hashes,
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope="Move arithmetic, distinctness and rollback only; no completeness claim.")
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("passed", "traces", "replayed_moves",
                                            "moves_changing_point_degrees")}))


if __name__ == "__main__":
    main()
