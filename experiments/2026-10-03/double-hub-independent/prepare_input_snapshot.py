# Document:    Double Hub Residual Tree Inputs
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import gzip
import hashlib
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

source = Path("experiments/scratch/double-hub-lp-20261003/certificates.json.gz")
raw = source.read_bytes()
certificates = json.loads(gzip.decompress(raw))
blocks = list(itertools.combinations(range(1, 17), 5))
triples = list(itertools.combinations(range(1, 17), 3))
ranks = {t: i for i, t in enumerate(triples)}
block_triples = [tuple(ranks[t] for t in itertools.combinations(b, 3)) for b in blocks]
cases = []
for case_id in (7, 145):
    source_case = certificates["cases"][case_id]
    certificate = source_case["certificate"]
    denominator = math.lcm(*(w[2] for w in certificate["weights"]))
    weights = {tid: numerator * (denominator // divisor)
               for tid, numerator, divisor in certificate["weights"]}
    bound = Fraction(sum(weights.values()), denominator)
    assert [bound.numerator, bound.denominator] == certificate["lower_bound"]
    capacities = [sum(weights.get(t, 0) for t in ts) for ts in block_triples]
    cutoff = sum(weights.values()) - 31 * denominator
    pool = [i for i, cap in enumerate(capacities) if cap >= cutoff]
    retained = source_case["retained_block_ids"]
    cases.append({
        "identifier": source_case["identifier"], "source_case_id": case_id,
        "removed": [], "retained_block_ids": retained,
        "retained_core_blocks": [blocks[i] for i in retained],
        "denominator": denominator, "weights": sorted(weights.items()),
        "exact_lower_bound": [bound.numerator, bound.denominator],
        "allowed_block_ids": pool, "allowed_blocks": [blocks[i] for i in pool],
        "allowed_block_count": len(pool), "minimum_block_load_numerator": cutoff,
    })
    print(json.dumps({"case": case_id, "global_pool": len(pool),
                      "anchor_blocks_in_pool": sum(bool(set(blocks[i]) & {1, 2})
                                                   for i in pool)}))
body = {"additional_blocks_allowed": 32, "candidates": cases,
        "source_certificate_path": str(source),
        "source_certificate_sha256": hashlib.sha256(raw).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "All global additions to each explicit retained32-block union; no global claim"}
output = Path("experiments/scratch/double-hub-trees-20261003")
output.mkdir(exist_ok=True)
(output / "input.json.gz").write_bytes(gzip.compress(
    (json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n").encode(), mtime=0))
