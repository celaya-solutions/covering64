# Document:    Independent eight-removal exact pool audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2718342053944ad0df2ceb1ec46b5880fef871f68d34e9eff1e2d3a007aab42d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import hashlib
import json
from fractions import Fraction
from itertools import combinations
from pathlib import Path

root = Path(__file__).resolve().parents[2] / "2026-10-03/core-eight-scan"
scan = json.loads(gzip.decompress((root / "scan.json.gz").read_bytes()))
pool_path = root / "dual-reduced-candidates.json.gz"
reduced = json.loads(gzip.decompress(pool_path.read_bytes()))
assert reduced["additional_blocks_allowed"] == 12
triples = list(combinations(range(1, 17), 3))
blocks = list(combinations(range(1, 17), 5))
block_index = {block: i for i, block in enumerate(blocks)}
core = [tuple(block) for block in scan["core_blocks"]]
expected = {tuple(case["removed"]) for case in scan["cases"]}
minimum_bound = None
sizes = []
for case in reduced["candidates"]:
    removed = tuple(case["removed"])
    assert removed in expected
    expected.remove(removed)
    retained = [block for i, block in enumerate(core, 1) if i not in removed]
    assert case["retained_core_blocks"] == [list(block) for block in retained]
    assert case["retained_block_ids"] == [block_index[block] for block in retained]
    assert len(retained) == 52
    covered = {t for block in retained for t in combinations(block, 3)}
    denominator = case["denominator"]
    assert type(denominator) is int and denominator > 0
    weights = {}
    for index, numerator in case["weights"]:
        assert type(index) is int and 0 <= index < len(triples)
        assert type(numerator) is int and 0 < numerator <= denominator
        triple = triples[index]
        assert triple not in weights and triple not in covered
        weights[triple] = numerator
    loads = [sum(weights.get(t, 0) for t in combinations(block, 3)) for block in blocks]
    assert max(loads) <= denominator
    total = sum(weights.values())
    assert 11 * denominator < total <= 12 * denominator
    bound = Fraction(total, denominator)
    assert case["exact_lower_bound"] == [bound.numerator, bound.denominator]
    cutoff = total - 11 * denominator
    assert case["minimum_block_load_numerator"] == cutoff
    allowed = [i for i, load in enumerate(loads) if load >= cutoff]
    assert case["allowed_block_ids"] == allowed
    assert case["allowed_blocks"] == [list(blocks[i]) for i in allowed]
    assert case["allowed_block_count"] == len(allowed)
    assert not set(allowed) & set(case["retained_block_ids"])
    sizes.append(len(allowed))
    minimum_bound = bound if minimum_bound is None else min(minimum_bound, bound)
assert not expected
print(json.dumps({"valid_reduced_pools": True, "verified_classes": len(sizes),
    "smallest_reconstructed_bound": [minimum_bound.numerator, minimum_bound.denominator],
    "smallest_pool": min(sizes), "largest_pool": max(sizes),
    "pool_sha256": hashlib.sha256(pool_path.read_bytes()).hexdigest(),
    "claim": ("All possible completions retained for these 155 specified neighborhoods; "
              "no feasibility claim")}, indent=2))
