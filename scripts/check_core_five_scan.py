# Document:    Standalone restricted five-removal scan checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      a404893c5aa57f22039f283e32647dc919857d8a510e5b8bd391544b628fd156
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check the exact scanned family and rational duals without solver libraries."""

import argparse
import gzip
import json
import sys
from fractions import Fraction
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_core_orbit_certificate import (  # noqa: E402
    check_data,
    core_actions,
    integer,
    require,
)


def check_scan(data, parent_data):
    require(check_data(parent_data)["complete_obstruction"], "Incomplete source proof")
    require(isinstance(data, dict) and data.get("schema") == "restricted-core-five-removal-scan-v1",
            "Wrong scan schema")
    require(data.get("core_blocks") == parent_data["core_blocks"], "Wrong core")
    require(data.get("core_sha256") == parent_data["core_sha256"], "Wrong core hash")
    require(data.get("target") == 64 and data.get("removed_count") == 5
            and data.get("additional_blocks_allowed") == 9, "Wrong scan parameters")
    core = [tuple(b) for b in data["core_blocks"]]
    actions = core_actions(core, data.get("generators"))
    parents = data.get("parent_removed_sets")
    require(isinstance(parents, list) and 1 <= len(parents) <= 100, "Bad parent sets")
    ordered = sorted(parent_data["cases"], key=lambda c: (
        Fraction(sum(n for _, n in c["weights"]), c["denominator"]), c["removed"]))
    require(parents == [c["removed"] for c in ordered[:len(parents)]],
            "Parents are not the specified lowest-bound representatives")
    expected = set()
    for parent in parents:
        for extra in range(1, 61):
            if extra not in parent:
                removed = [*parent, extra]
                expected.add(min(tuple(sorted(action[i - 1] for i in removed))
                                 for action in actions))
    triples = list(combinations(range(1, 17), 3))
    triple_ids = {t: i for i, t in enumerate(triples)}
    coverage = [tuple(triple_ids[t] for t in combinations(b, 3))
                for b in combinations(range(1, 17), 5)]
    core_coverage = [set(triple_ids[t] for t in combinations(b, 3)) for b in core]
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == len(expected), "Wrong case count")
    candidates, minimum = [], None
    for case in cases:
        removed = tuple(case["removed"])
        require(all(type(i) is int for i in removed), "Bad removal indices")
        require(removed in expected, "Unexpected or duplicate removal class")
        expected.remove(removed)
        denominator = integer(case["denominator"], 1, 10**12, "Bad denominator")
        retained = set().union(*(c for i, c in enumerate(core_coverage, 1) if i not in removed))
        weights = {}
        for index, numerator in case["weights"]:
            index = integer(index, 0, 559, "Bad triple rank")
            numerator = integer(numerator, 1, denominator, "Bad numerator")
            require(index not in weights and index not in retained, "Invalid triple support")
            weights[index] = numerator
        require(all(sum(weights.get(t, 0) for t in block) <= denominator for block in coverage),
                "Block capacity exceeded")
        bound = Fraction(sum(weights.values()), denominator)
        require(case["lower_bound"] == [bound.numerator, bound.denominator], "Wrong bound")
        minimum = bound if minimum is None else min(bound, minimum)
        if bound <= 9:
            candidates.append({"removed": removed, "lower_bound": case["lower_bound"]})
    require(not expected, "Missing removal class")
    return {"valid_scan": True, "scope": "Only subgroup classes of the listed parent extensions",
            "parent_count": len(parents), "scanned_classes": len(cases),
            "certified_impossible_classes": len(cases) - len(candidates),
            "lp_uncertified_candidates": candidates,
            "minimum_exact_dual": [minimum.numerator, minimum.denominator],
            "all_five_removals_checked": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scan", type=Path)
    parser.add_argument("--source", type=Path,
                        default=ROOT / "experiments/2026-10-03/core-orbit/core-remove-4.json.gz")
    args = parser.parse_args()
    try:
        data = json.loads(gzip.decompress(args.scan.read_bytes()))
        parent_data = json.loads(gzip.decompress(args.source.read_bytes()))
        result = check_scan(data, parent_data)
    except (ValueError, TypeError, KeyError, OSError, EOFError) as error:
        print(json.dumps({"valid_scan": False, "error": str(error)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
