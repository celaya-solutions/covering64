# Document:    Standalone core completion triangle obstruction checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e96c90bb68b364a60d2e346eab0d2059e81b2309486090eece48e3b6e7a27354
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check an exact residual dual and a three-block contradiction using only stdlib."""

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

CORE_HASH = "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical_labels(values, size):
    require(isinstance(values, list) and len(values) == size, "Bad label list length")
    require(all(type(p) is int and 1 <= p <= 16 for p in values), "Bad point label")
    require(values == sorted(set(values)), "Noncanonical label list")
    return tuple(values)


def check_data(data):
    require(isinstance(data, dict) and data.get("schema") == "core-five-triangle-v1",
            "Wrong certificate schema")
    core = data.get("core_blocks")
    require(isinstance(core, list) and len(core) == 60, "Wrong core length")
    core = [canonical_labels(b, 5) for b in core]
    require(core == sorted(set(core)), "Wrong core order or duplicate blocks")
    raw = "".join(" ".join(map(str, b)) + "\n" for b in core).encode("ascii")
    require(hashlib.sha256(raw).hexdigest() == CORE_HASH == data.get("core_sha256"),
            "Wrong fixed core")
    removed = data.get("removed")
    require(isinstance(removed, list) and len(removed) == 5, "Wrong removal count")
    require(all(type(i) is int and 1 <= i <= 60 for i in removed), "Bad removal index")
    require(removed == sorted(set(removed)), "Duplicate or unordered removal indices")
    retained = [b for i, b in enumerate(core, 1) if i not in removed]
    triples = list(combinations(range(1, 17), 3))
    missing = set(triples) - {t for b in retained for t in combinations(b, 3)}
    denominator = data.get("denominator")
    require(type(denominator) is int and 1 <= denominator <= 10**12, "Bad denominator")
    raw_weights = data.get("weights")
    require(isinstance(raw_weights, list), "Missing dual weights")
    weights = {}
    for entry in raw_weights:
        require(isinstance(entry, list) and len(entry) == 2, "Bad weight entry")
        index, numerator = entry
        require(type(index) is int and 0 <= index < 560, "Bad triple rank")
        require(type(numerator) is int and 1 <= numerator <= denominator, "Bad numerator")
        triple = triples[index]
        require(triple in missing and triple not in weights, "Bad dual support")
        weights[triple] = numerator
    require(sum(weights.values()) == 9 * denominator, "Dual bound must equal nine")
    blocks = list(combinations(range(1, 17), 5))
    loads = [sum(weights.get(t, 0) for t in combinations(b, 3)) for b in blocks]
    require(max(loads) <= denominator, "Dual block capacity exceeded")
    tight = [block for block, load in zip(blocks, loads) if load == denominator]
    special = data.get("special_blocks")
    require(isinstance(special, list) and len(special) == 3, "Need three special blocks")
    special = [canonical_labels(b, 5) for b in special]
    require(len(set(special)) == 3 and set(special) <= set(tight), "Invalid special blocks")
    required = data.get("required_triples")
    conflicts = data.get("conflict_triples")
    require(isinstance(required, list) and len(required) == 3, "Need three required triples")
    require(isinstance(conflicts, list) and len(conflicts) == 3, "Need three conflict triples")
    details = []
    for index, (left, right) in enumerate(combinations(range(3), 2)):
        triple = canonical_labels(required[index], 3)
        require(triple in missing, "Required triple already covered")
        carriers = {block for block in tight if set(triple) <= set(block)}
        require(carriers == {special[left], special[right]}, "Wrong exact carrier pair")
        conflict = canonical_labels(conflicts[index], 3)
        require(conflict in weights, "Conflict triple must have positive dual weight")
        require(set(conflict) <= set(special[left]) & set(special[right]),
                "Conflict triple not shared by the stated blocks")
        details.append({"pair": [left + 1, right + 1], "required_triple": triple,
                        "conflict_triple": conflict})
    require(len(set(map(tuple, required))) == 3, "Required triples must be distinct")
    return {
        "valid_certificate": True, "complete_obstruction": True,
        "scope": "Only covers containing the specified55 retained core blocks",
        "removed": removed, "retained_core_blocks": len(retained),
        "additional_blocks_allowed": 9, "missing_triples": len(missing),
        "positive_weight_triples": len(weights), "exact_dual_bound": [9, 1],
        "all_possible_blocks_checked": len(blocks), "tight_blocks": len(tight),
        "special_blocks": special, "triangle_checks": details,
        "contradiction": ("Coverage needs at least two special blocks; "
                          "exact weighted coverage permits at most one"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    args = parser.parse_args()
    try:
        result = check_data(json.loads(args.certificate.read_text()))
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(json.dumps({"valid_certificate": False, "error": str(error)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
