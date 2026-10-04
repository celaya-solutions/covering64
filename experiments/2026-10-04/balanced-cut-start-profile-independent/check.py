# Document:    Weighted Balanced Cut Start Profile Independent Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c22bfec369a396a14879d48236980edaf0e637aae5afbc4715cacd3c5c891d78
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Finite weighted bisection counts; no solver or optimizer calls."""

import hashlib
import itertools
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STARTS = (
    (
        "experiments/2026-10-04/weak-pair-h9-d23-neutral-queue-runtime-independent/"
        "family-a0a737c4010f68fc.txt",
        "a0a737c4010f68fcd5bfba8ccc7c20b4b8d9f06a96bb0086c7a63dbfc43f5ecc",
    ),
    (
        "experiments/2026-10-04/native-five-core-record-pilot/"
        "seed-2026105602/search-final-weak64.txt",
        "85f6e38a537691442cf6097a68b1364a755ac1ba8312d61adfc88c26abb6a90e",
    ),
)


def profile(relative, expected):
    path = ROOT / relative
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64
    assert all(len(b) == len(set(b)) == 5 and all(1 <= x <= 16 for x in b) for b in blocks)
    assert all(tuple(sorted(b)) == b for b in blocks)
    pairs = Counter(p for b in blocks for p in itertools.combinations(b, 2))
    triples = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    excess = {p: pairs[p] - 5 for p in itertools.combinations(range(1, 17), 2)}
    assert min(excess.values()) >= 0 and sum(excess.values()) == 40
    holes = set(itertools.combinations(range(1, 17), 3)) - set(triples)
    histogram = Counter()
    first_maximum = None
    for tail in itertools.combinations(range(2, 17), 7):
        left = {1, *tail}
        cut = sum(w for (u, v), w in excess.items() if (u in left) != (v in left))
        same_holes = sum(len(set(t) & left) in (0, 3) for t in holes)
        incidence = sum(n for t, n in triples.items() if len(set(t) & left) in (0, 3))
        repeated = sum(n - 1 for t, n in triples.items() if len(set(t) & left) in (0, 3))
        assert cut % 2 == 0
        assert 2 * incidence == 320 - 3 * cut
        assert 2 * repeated == 96 - 3 * cut + 2 * same_holes
        histogram[cut] += 1
        if first_maximum is None or cut > first_maximum["cut_weight"]:
            first_maximum = {
                "left": sorted(left),
                "right": sorted(set(range(1, 17)) - left),
                "cut_weight": cut,
                "same_half_holes": same_holes,
                "same_half_repeated_excess": repeated,
            }
    assert sum(histogram.values()) == 6435
    return {
        "path": relative, "sha256": expected, "holes": len(holes),
        "pair_floor": min(pairs.values()), "pair_excess_total": sum(excess.values()),
        "bisections": sum(histogram.values()), "cut_histogram": dict(sorted(histogram.items())),
        "maximum_cut": max(histogram), "maximizing_bisections": histogram[max(histogram)],
        "violations_of_full_cover_necessary_bound": sum(n for w, n in histogram.items() if w > 32),
        "first_maximum": first_maximum,
    }


def main():
    identities = []
    for k in range(6):
        pair_count = math.comb(k, 2) + math.comb(5 - k, 2)
        triple_count = math.comb(k, 3) + math.comb(5 - k, 3)
        assert 2 * triple_count == 3 * pair_count - 10
        identities.append({"left_block_points": k, "pairs": pair_count, "triples": triple_count})
    result = {
        "passed": True, "optimizer_launches": 0, "block_type_identities": identities,
        "existing_simple_regular_case": "scripts/check_independent_clebsch.py:99-125",
        "full_cover_necessary_bound": 32,
        "scope": ("Weighted pair excess, no regularity assumption; "
                  "necessary only. Neither start excluded."),
        "families": [profile(*row) for row in STARTS],
    }
    target = HERE / "profile.json"
    encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    if target.exists():
        assert target.read_bytes() == encoded
    else:
        target.write_bytes(encoded)
    print(json.dumps({"passed": True, "profile_sha256": hashlib.sha256(encoded).hexdigest()}))


if __name__ == "__main__":
    main()
