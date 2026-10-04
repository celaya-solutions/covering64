# Document:    Independent Third Core Transport Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      885f3207bffd6b7234a30b6a3e14ade0fe8d147d9e0cb93b1cf3beb0d57d4cc3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check one explicit relabeling and its exact transported core cap."""

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
WITNESS = DAY / "six-hole-relabeled-core-transport/witness.json"
CORE = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
CAP = DAY / "core-cap-independent/audit.json"
POST = DAY / "six-hole-strong-core-release-independent/postcheck.json"
FINAL = DAY / "six-hole-strong-core-release/full-4368/final-response.txt"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {b: i for i, b in enumerate(BLOCKS)}
TRIPLES = list(itertools.combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def parse(path, size):
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == size and blocks == sorted(blocks)
    assert all(b in RANK for b in blocks)
    return blocks


def check(witness, core, candidate):
    mapping = witness["map_images"]
    assert len(mapping) == 16 and all(type(p) is int for p in mapping)
    assert sorted(mapping) == list(range(1, 17))
    mapped = sorted(tuple(sorted(mapping[p - 1] for p in b)) for b in core)
    assert len(mapped) == len(set(mapped)) == 60
    ids = sorted(RANK[b] for b in mapped)
    selected = sorted(RANK[b] for b in candidate)
    common = sorted(set(ids) & set(selected))
    assert witness["transported_core_blocks"] == [list(b) for b in mapped]
    assert witness["transported_core_global_ids"] == ids
    assert witness["candidate_global_ids"] == selected
    assert witness["intersection_global_ids"] == common
    assert witness["overlap"] == len(common) == 60
    assert witness["valid_transported_core_cap"] == 55 and witness["violates_transported_core_cap"]
    inverse = {image: original for original, image in enumerate(mapping, 1)}
    assert sorted(tuple(sorted(inverse[p] for p in b)) for b in mapped) == core
    mapped_blocks = [tuple(sorted(mapping[p - 1] for p in b)) for b in BLOCKS]
    mapped_triples = [tuple(sorted(mapping[p - 1] for p in t)) for t in TRIPLES]
    assert set(mapped_blocks) == set(BLOCKS) and set(mapped_triples) == set(TRIPLES)
    assert all(
        {tuple(sorted(mapping[p - 1] for p in t)) for t in itertools.combinations(block, 3)}
        == set(itertools.combinations(image, 3))
        for block, image in zip(BLOCKS, mapped_blocks, strict=True)
    )
    return ids


def main():
    assert not (HERE / "audit.json").exists()
    assert sha(WITNESS) == "38bec1ea37046d37aaed0251a214523886cfa4a5f3ccfe3f99d0f6b0a2ca73c5"
    assert sha(CAP) == "fec461fad7b3f53fade9beecec77c7146487e02f5bbb36f543f642d190edc5a8"
    assert sha(POST) == "a2af3ec3400bcf2102941e6de69e53f253549717fbd0112a455b5d1be85a5741"
    assert sha(FINAL) == "0c5147f1c3824d40437853ed0a8c75ef6b9b393926ac7f1b47f2724d507f0c78"
    cap = read(CAP)
    assert cap["passed"] and cap["recommended_upper_bound"] == 55
    for relative, checksum in cap["sources"].items():
        assert sha(ROOT / relative) == checksum
    core, candidate = parse(CORE, 60), parse(FINAL, 64)
    witness = read(WITNESS)
    ids = check(witness, core, candidate)
    previous = read(POST)
    assert previous["passed"] and previous["cases"][1]["final"]["sha256"] == sha(FINAL)
    states = []
    for case in previous["cases"]:
        for state in case["saved"] + [case["final"]]:
            path = ROOT / state["path"]
            assert sha(path) == state["sha256"]
            actual = sorted(RANK[b] for b in parse(path, 64))
            assert actual == state["ids"]
            overlap = len(set(actual) & set(ids))
            states.append(
                {
                    "path": state["path"],
                    "sha256": state["sha256"],
                    "holes": state["holes"],
                    "third_core_overlap": overlap,
                    "violates_cap55": overlap > 55,
                }
            )
    controls = []
    for label, mutate in (
        ("nonpermutation", lambda d: d["map_images"].__setitem__(0, d["map_images"][1])),
        ("wrong_map", lambda d: d["map_images"].reverse()),
        ("wrong_core_id", lambda d: d["transported_core_global_ids"].__setitem__(0, 0)),
        ("wrong_overlap", lambda d: d.__setitem__("overlap", 59)),
        ("unproved_cap54", lambda d: d.__setitem__("valid_transported_core_cap", 54)),
    ):
        damaged = json.loads(json.dumps(witness))
        mutate(damaged)
        try:
            check(damaged, core, candidate)
        except AssertionError:
            controls.append(label)
        else:
            raise AssertionError(f"damaged control accepted: {label}")
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "map_images": witness["map_images"],
        "core_global_ids": ids,
        "recommended_upper_bound": 55,
        "candidate_overlap": 60,
        "block_bijection_size": 4368,
        "triple_bijection_size": 560,
        "incidences_checked": 43680,
        "sources": {
            str(p.relative_to(ROOT)): sha(p)
            for p in [Path(__file__), WITNESS, CORE, CAP, POST, FINAL]
        },
        "previous_states": states,
        "damaged_controls_rejected": controls,
        "scope": (
            "Exact verification of this one explicit core transport. The already checked cap55 "
            "transports by the verified full incidence bijection. No exhaustive map-search claim "
            "is required or certified here. The candidate is a known three-hole noncover."
        ),
    }
    (HERE / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "audit_sha256": sha(HERE / "audit.json"),
                "overlap": 60,
                "recommended_upper_bound": 55,
            }
        )
    )


if __name__ == "__main__":
    main()
