# Document:    Independent Bitmask Audit of Point Twelve Repair Dual
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d1fd3bccb7c4474fa159de29fadbb7e49653c9b4ada4212939ee859e44ec812b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import gzip
import hashlib
import json
import pathlib
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def labels(mask):
    return tuple(p + 1 for p in range(16) if mask & (1 << p))


def check(initial, metadata, dual):
    rows = [tuple(map(int, line.split())) for line in initial.splitlines()]
    require(len(rows) == len(set(rows)) == 64, "seed cardinality")
    require(
        all(
            len(r) == 5 and r == tuple(sorted(set(r))) and 1 <= min(r) and max(r) <= 16
            for r in rows
        ),
        "seed structure",
    )
    seed = {sum(1 << (p - 1) for p in row) for row in rows}
    blocks = sorted((m for m in range(1 << 16) if m.bit_count() == 5), key=labels)
    triples = sorted((m for m in range(1 << 16) if m.bit_count() == 3), key=labels)
    point12 = 1 << 11
    retained = sorted((b for b in seed if not b & point12), key=labels)
    candidates = [b for b in blocks if b & point12]
    missing = [i for i, t in enumerate(triples) if not any(b & t == t for b in retained)]
    require(metadata["release_points"] == [12], "release scope")
    require(metadata["retained_ids"] == [blocks.index(b) for b in retained], "retained scope")
    require(
        metadata["candidate_ids"] == [i for i, b in enumerate(blocks) if b & point12],
        "candidate scope",
    )
    require(metadata["deficient_ids"] == missing, "deficiency scope")
    require(
        len(retained) == 44 and len(candidates) == 1365 and len(missing) == 171,
        "scope cardinalities",
    )
    require(metadata["addition_budget"] == dual["addition_budget"] == 20, "budget")
    denominator = dual["common_denominator"]
    require(type(denominator) is int and denominator > 0, "denominator")
    weights = dual["weights"]
    require(
        all(
            isinstance(row, list)
            and len(row) == 2
            and all(type(v) is int for v in row)
            and row[0] in missing
            and row[1] >= 0
            for row in weights
        ),
        "weight support",
    )
    require(
        weights == sorted(weights) and len(set(row[0] for row in weights)) == len(weights),
        "duplicate or unordered weights",
    )
    weighted_masks = [(triples[i], numerator) for i, numerator in weights]
    loads = [sum(n for t, n in weighted_masks if b & t == t) for b in candidates]
    require(max(loads) <= denominator, "column exceeds one")
    total = sum(n for _, n in weighted_masks)
    bound = Fraction(total, denominator)
    require(dual["bound"] == [bound.numerator, bound.denominator], "bound")
    require(dual["columns_checked"] == 1365, "column count")
    require(dual["proves_neighborhood_infeasible"] is True and bound > 20, "strict exclusion")
    return dict(
        valid=True,
        retained=44,
        deficient_triples=171,
        candidate_columns=1365,
        positive_weights=sum(n > 0 for _, n in weighted_masks),
        maximum_column_numerator=max(loads),
        numerator=total,
        denominator=denominator,
        lower_bound=[bound.numerator, bound.denominator],
        addition_budget=20,
        original_seed_missing=[labels(t) for t in triples if not any(b & t == t for b in seed)],
    )


def main():
    archive_path = ROOT / "point12.json.gz"
    raw = archive_path.read_bytes()
    archive = json.loads(gzip.decompress(raw))
    files = archive["files"]
    initial = files["initial.txt"]
    metadata = json.loads(files["metadata.json"])
    dual = json.loads(files["simplified-dual.json"])
    require(hashlib.sha256(initial.encode()).hexdigest() == metadata["input_sha256"], "seed hash")
    result = check(initial, metadata, dual)
    controls = []
    for name, change in (
        ("negative weight", lambda d: d["weights"][0].__setitem__(1, -1)),
        ("overloaded column", lambda d: d["weights"][0].__setitem__(1, 55)),
        ("duplicate weight", lambda d: d["weights"].append(d["weights"][0])),
        ("wrong bound", lambda d: d.__setitem__("bound", [43, 3])),
        ("wrong budget", lambda d: d.__setitem__("addition_budget", 21)),
        ("zero denominator", lambda d: d.__setitem__("common_denominator", 0)),
    ):
        damaged = copy.deepcopy(dual)
        change(damaged)
        try:
            check(initial, metadata, damaged)
        except ValueError:
            controls.append(dict(control=name, rejected=True))
        else:
            raise ValueError("damaged certificate accepted")
    result.update(
        archive_sha256=hashlib.sha256(raw).hexdigest(),
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        seed_sha256=hashlib.sha256(initial.encode()).hexdigest(),
        dual_sha256=hashlib.sha256(files["simplified-dual.json"].encode()).hexdigest(),
        damaged_controls=controls,
        method="Enumerate all 16-bit masks by population count; exact integer subset loads.",
        scope="Retain the 44 seed blocks avoiding point 12, and require every added block "
        "to contain point 12. This excludes that repair neighborhood only, "
        "not every completion retaining those 44 blocks.",
    )
    (ROOT / "point12-bitmask-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
