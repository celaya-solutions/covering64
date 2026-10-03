# Document:    Standalone certificate check for the fixed 60-block obstruction
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      4f0860d2327ff076a8045070d94e081d2280b24e20018d5c6fdf752f88cd43b4
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check a restricted obstruction with standard-library enumeration, no solver."""

import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAPPINGS = {
    2: [1, 2, 12, 14, 3, 5, 16, 8, 11, 4, 10, 6, 15, 9, 7, 13],
    9: [1, 2, 10, 13, 4, 9, 16, 7, 12, 8, 15, 3, 11, 14, 5, 6],
}


def read_cover(path):
    blocks = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        block = tuple(map(int, line.split()))
        assert len(block) == len(set(block)) == 5
        assert set(block) <= set(range(1, 17))
        blocks.append(tuple(sorted(block)))
    assert len(blocks) == len(set(blocks)) == 65
    assert {t for b in blocks for t in combinations(b, 3)} == set(
        combinations(range(1, 17), 3))
    return sorted(blocks)


def split_core(blocks):
    counts = Counter(t for b in blocks for t in combinations(b, 3))
    support = {b: tuple(sorted({v for t in combinations(b, 3)
                               if counts[t] == 1 for v in t})) for b in blocks}
    core = [b for b in blocks if len(support[b]) == 5]
    supports = sorted(support[b] for b in blocks if len(support[b]) < 5)
    assert len(core) == 60 and len(supports) == 5
    assert len(set(supports)) == 5 and all(len(s) == 4 for s in supports)
    return core, supports


def canonical_hash(blocks):
    data = "".join(" ".join(map(str, b)) + "\n" for b in sorted(blocks)).encode()
    return hashlib.sha256(data).hexdigest()


def compute(baseline):
    blocks = read_cover(baseline)
    core, supports = split_core(blocks)
    all_triples = set(combinations(range(1, 17), 3))
    missing = all_triples - {t for b in core for t in combinations(b, 3)}
    special = set.intersection(*(set(s) for s in supports))
    assert special == {7}
    groups = [tuple(v for v in s if v != 7) for s in supports]
    assert sorted(v for g in groups for v in g) == [v for v in range(1, 17) if v != 7]
    expected = {tuple(sorted((7, *pair))) for g in groups for pair in combinations(g, 2)}
    assert missing == expected and len(missing) == 15
    all_blocks = list(combinations(range(1, 17), 5))
    assert len(all_blocks) == 4368
    gains = {b: len(set(combinations(b, 3)) & missing) for b in all_blocks}
    hist = dict(sorted(Counter(gains.values()).items()))
    assert hist == {0: 3408, 1: 810, 2: 90, 3: 60}
    choices = [[b for b in all_blocks if set(s) <= set(b)] for s in supports]
    assert all(len(c) == 12 for c in choices)
    assert set(b for c in choices for b in c) == {b for b, gain in gains.items() if gain == 3}
    assert len(set(b for c in choices for b in c)) == 60
    # Every choice in a group covers precisely that group's three missing triples.
    for group, candidates in zip(groups, choices):
        wanted = {tuple(sorted((7, *p))) for p in combinations(group, 2)}
        assert all(set(combinations(b, 3)) & missing == wanted for b in candidates)
        assert not set(candidates) & set(core)
    mappings = []
    for point, values in MAPPINGS.items():
        other, _ = split_core(read_cover(HERE / f"link-at-{point}-65.txt"))
        assert sorted(values) == list(range(1, 17))
        mapped = {tuple(sorted(values[v - 1] for v in b)) for b in core}
        assert mapped == set(other)
        mappings.append({"target": f"link-at-{point}-65.txt", "images_of_1_to_16": values,
                         "mapped_core_sha256": canonical_hash(other)})
    # Count only, without storing or enumerating the Cartesian product.
    family_count = 1
    for c in choices:
        family_count *= len(c)
    assert family_count == 248832
    return {
        "scope": "Only covers that retain all 60 listed core blocks; not unrestricted",
        "baseline_sha256": canonical_hash(blocks), "core_sha256": canonical_hash(core),
        "core_blocks": core, "missing_triples": sorted(missing),
        "special_point": 7, "three_point_groups": groups, "four_point_supports": supports,
        "all_candidate_blocks_checked": len(all_blocks), "residual_gain_histogram": hist,
        "maximum_residual_gain": 3, "minimum_added_blocks": 5,
        "minimum_total_blocks_retaining_core": 65,
        "completion_choices_per_support": choices, "completion_family_size": family_count,
        "core_isomorphisms": mappings,
    }


def main():
    if not __debug__:
        raise SystemExit("Run without Python -O; certificate assertions must be enabled")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=ROOT / "data/baselines/belic-1997.txt")
    parser.add_argument("--certificate", type=Path, default=HERE / "fixed-core-certificate.json")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    expected = json.loads(json.dumps(compute(args.baseline)))
    if args.write:
        args.certificate.write_text(json.dumps(expected, indent=2) + "\n")
    assert json.loads(args.certificate.read_text()) == expected, "Damaged certificate"
    print(json.dumps({"verified": True, "scope": expected["scope"],
                      "fixed_core": 60, "uncovered": 15, "max_gain": 3,
                      "required_added_blocks": 5, "family_size": 248832}))


if __name__ == "__main__":
    main()
