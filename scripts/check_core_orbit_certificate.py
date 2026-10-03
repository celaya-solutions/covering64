# Document:    Standalone symmetry-reduced residual dual certificate checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      82feef99732751fec5666c71ff43cdd5af7c9adf0ea0c8afbc951cbcf2e32210
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check exact duals and complete removal-orbit coverage without solver libraries."""

import argparse
import gzip
import hashlib
import json
from collections import deque
from fractions import Fraction
from itertools import combinations
from pathlib import Path

CORE_HASH = "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, low, high, message):
    require(type(value) is int and low <= value <= high, message)
    return value


def canonical_hash(blocks):
    data = "".join(" ".join(map(str, b)) + "\n" for b in blocks).encode("ascii")
    return hashlib.sha256(data).hexdigest()


def core_actions(core, generators):
    identity = tuple(range(1, 17))
    require(isinstance(generators, list) and 1 <= len(generators) <= 60,
            "Missing or excessive generators")
    for generator in generators:
        require(isinstance(generator, list) and len(generator) == 16,
                "Bad point permutation length")
        require(all(type(p) is int for p in generator) and sorted(generator) == list(identity),
                "Bad point permutation")
    group, queue = {identity}, deque([identity])
    while queue:
        current = queue.popleft()
        for generator in generators:
            result = tuple(generator[p - 1] for p in current)
            if result not in group:
                group.add(result)
                queue.append(result)
        require(len(group) <= 60, "Unexpected subgroup size")
    require(len(group) == 60, "Expected certified subgroup of order 60")
    lookup = {block: i + 1 for i, block in enumerate(core)}
    actions = []
    for permutation in sorted(group):
        images = [tuple(sorted(permutation[p - 1] for p in block)) for block in core]
        require(set(images) == set(core), "Point action does not preserve core")
        actions.append(tuple(lookup[block] for block in images))
    return actions


def check_data(data):
    require(isinstance(data, dict) and data.get("schema") == "core-orbit-dual-v1",
            "Unknown certificate schema")
    require(data.get("target") == 64 and type(data.get("target")) is int, "Wrong target")
    removed_count = integer(data.get("removed_count"), 1, 4, "Unsupported removal count")
    core = data.get("core_blocks")
    require(isinstance(core, list) and len(core) == 60, "Core must have 60 blocks")
    for block in core:
        require(isinstance(block, list) and len(block) == 5, "Bad core block")
        require(all(type(p) is int and 1 <= p <= 16 for p in block), "Bad point label")
        require(block == sorted(set(block)), "Core block not canonical")
    core = [tuple(block) for block in core]
    require(core == sorted(set(core)), "Core order or distinctness invalid")
    require(canonical_hash(core) == CORE_HASH == data.get("core_sha256"), "Wrong fixed core")
    actions = core_actions(core, data.get("generators"))
    triples = list(combinations(range(1, 17), 3))
    triple_id = {triple: i for i, triple in enumerate(triples)}
    blocks = list(combinations(range(1, 17), 5))
    coverage = [tuple(triple_id[t] for t in combinations(block, 3)) for block in blocks]
    containing = [[] for _ in triples]
    for block, covered in enumerate(coverage):
        for triple in covered:
            containing[triple].append(block)
    core_coverage = [set(triple_id[t] for t in combinations(block, 3)) for block in core]
    unseen = set(combinations(range(1, 61), removed_count))
    total = len(unseen)
    cases = data.get("cases")
    require(isinstance(cases, list) and 1 <= len(cases) <= total, "Missing or excessive cases")
    threshold = removed_count + 4
    uncertified = []
    minimum = None
    for number, case in enumerate(cases):
        require(isinstance(case, dict), "Bad case")
        removed = case.get("removed")
        require(isinstance(removed, list) and len(removed) == removed_count, "Bad removal set")
        require(all(type(i) is int and 1 <= i <= 60 for i in removed), "Bad block index")
        require(removed == sorted(set(removed)), "Removal set must be canonical")
        orbit = {tuple(sorted(action[i - 1] for i in removed)) for action in actions}
        require(orbit <= unseen, "Overlapping or duplicate removal orbits")
        orbit_size = integer(case.get("orbit_size"), 1, 60, "Bad orbit size")
        require(orbit_size == len(orbit), "Incorrect orbit size")
        unseen -= orbit
        denominator = integer(case.get("denominator"), 1, 10**12, "Bad denominator")
        weights = case.get("weights")
        require(isinstance(weights, list), "Missing weights")
        retained_coverage = set().union(*(c for i, c in enumerate(core_coverage, 1)
                                          if i not in removed))
        numerators = {}
        for weight in weights:
            require(isinstance(weight, list) and len(weight) == 2, "Bad weight entry")
            triple = integer(weight[0], 0, 559, "Bad lexicographic triple index")
            numerator = integer(weight[1], 1, denominator, "Bad nonnegative dual weight")
            require(triple not in numerators, "Duplicate weighted triple")
            require(triple not in retained_coverage, "Weight on an already covered triple")
            numerators[triple] = numerator
        loads = [0] * len(blocks)
        for triple, numerator in numerators.items():
            for block in containing[triple]:
                loads[block] += numerator
        require(max(loads) <= denominator, "Dual exceeds an added block's capacity")
        bound = Fraction(sum(numerators.values()), denominator)
        minimum = bound if minimum is None else min(minimum, bound)
        if bound <= threshold:
            uncertified.append({"case": number, "removed": removed,
                                "lower_bound": [bound.numerator, bound.denominator]})
    require(not unseen, "Some removal sets have no transported certificate")
    require(type(data.get("claimed_complete")) is bool, "Missing completeness declaration")
    complete = not uncertified
    require(data["claimed_complete"] == complete, "False completeness declaration")
    result = {"valid_certificate": True, "complete_obstruction": complete,
              "scope": "Only covers retaining the specified core subset; not unrestricted",
              "removed_count": removed_count, "representatives": len(cases),
              "all_removal_sets_checked": total, "subgroup_order": len(actions),
              "additional_blocks_allowed": threshold,
              "minimum_exact_dual_bound": [minimum.numerator, minimum.denominator],
              "uncertified_representatives": uncertified}
    if complete:
        result["maximum_core_blocks_in_any_64_cover"] = 59 - removed_count
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    args = parser.parse_args()
    try:
        raw = args.certificate.read_bytes()
        data = json.loads(gzip.decompress(raw) if args.certificate.suffix == ".gz" else raw)
        result = check_data(data)
    except (ValueError, TypeError, KeyError, OSError, EOFError) as error:
        print(json.dumps({"valid_certificate": False, "error": str(error)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["complete_obstruction"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
