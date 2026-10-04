# Document:    Independent Replay of the 128 Block Union Bound
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      646af421974838d46f2f63f3b59cd7a0e12d8720cda90c8849ad9e4a23770d17
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reconstruct every certificate support directly from the two source families."""

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    certificate_path = HERE / "certificate.json"
    certificate = json.loads(certificate_path.read_text())
    universe = list(itertools.combinations(range(1, 17), 5))
    block_ids = {block: index for index, block in enumerate(universe)}
    families = []
    for source in certificate["sources"]:
        path = ROOT / source["path"]
        assert sha(path) == source["sha256"]
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        assert len(blocks) == len(set(blocks)) == 64
        assert all(block in block_ids for block in blocks)
        ids = {block_ids[block] for block in blocks}
        assert sorted(ids) == source["ids"]
        families.append(ids)
    assert len(families) == 2 and not families[0].intersection(families[1])
    pool = families[0] | families[1]
    assert len(pool) == 128 and sorted(pool) == certificate["union_ids"]
    supports = {}
    for triple in itertools.combinations(range(1, 17), 3):
        supports[triple] = {
            index for index in pool if set(triple).issubset(universe[index])
        }
    assert all(supports.values())
    used = set()
    selected_rows = certificate["forced_rows"] + certificate["matched_pair_rows"]
    assert len(certificate["forced_rows"]) == 19
    assert len(certificate["matched_pair_rows"]) == 54
    for number, row in enumerate(selected_rows):
        assert all(type(label) is int for label in row["triple"])
        assert all(type(index) is int for index in row["carrier_ids"])
        actual = supports[tuple(row["triple"])]
        assert sorted(actual) == row["carrier_ids"]
        assert len(actual) == (1 if number < 19 else 2)
        assert not used.intersection(actual)
        used.update(actual)
    bound = len(selected_rows)
    assert bound == certificate["selected_lower_bound"] == 73
    assert len(used) == 127
    result = {
        "passed": True,
        "certificate_sha256": sha(certificate_path),
        "replay_source_sha256": sha(Path(__file__)),
        "universe_blocks": len(universe),
        "pool_blocks": len(pool),
        "independently_reconstructed_supports": len(supports),
        "disjoint_support_rows": bound,
        "distinct_carriers_in_proof": len(used),
        "selected_block_lower_bound": bound,
        "optimizer_calls": 0,
        "scope": "Only complete covers contained in the pinned 128-block union.",
    }
    (HERE / "root-replay.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
