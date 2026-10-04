# Document:    Independent Heavy Link Odd Set Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Enumerate all8192 subsets, justify every omission, and compare all8096 added rows."""

import hashlib
import json
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FROZEN = ROOT / "experiments/scratch/four-seven-blossom-cuts-v1.0.0"
HELPER_SHA = "91e9166a89e5fa610cf970f16c17e829f809388c3f18a6070c7198a396438818"
BASE_SHA = {"cycle": "5cbaba3a581ab485a1ebd5adc3a328ff53c963a414fadc773bb9687abead02d9",
            "matching": "5f85a1cd9caa86742892e44c0632df0c99c0409bc3e69d0905e4924a08116b84"}
ANCHORS = ({1, 2, 3}, {5, 6, 7}, {9, 10, 11}, {13, 14, 15})


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_rows():
    blocks = list(combinations(range(1, 17), 5))
    indices = {block: i for i, block in enumerate(blocks)}
    reports, rows = [], []
    for group, anchors in enumerate(ANCHORS):
        outside = tuple(p for p in range(1, 17) if p not in anchors)
        hub = 4 * (group + 1)
        universe = set(outside)
        canonical, omitted, retained = set(), set(), []
        odd = 0
        for mask in range(1 << 13):
            subset = {p for i, p in enumerate(outside) if mask & (1 << i)}
            b_sum = len(subset) + int(hub in subset)
            if b_sum % 2 == 0:
                continue
            odd += 1
            complement = universe - subset
            other_b = len(complement) + int(hub in complement)
            require(b_sum + other_b == 14 and other_b % 2 == 1, "wrong degree complement")
            require((b_sum - 1) // 2 + (other_b - b_sum) // 2 == (other_b - 1) // 2,
                    "complement inequality not equivalent")
            if len(subset) > len(complement):
                continue
            subset_tuple = tuple(sorted(subset))
            canonical.add(subset_tuple)
            if len(subset) == 1:
                require(hub not in subset and b_sum == 1, "wrong singleton omission")
                omitted.add(subset_tuple)
                continue
            if len(subset) == 2:
                require(hub in subset and b_sum == 3, "wrong unit-bound omission")
                omitted.add(subset_tuple)
                continue
            require(3 <= len(subset) <= 6, "unexpected retained size")
            ids = sorted(indices[tuple(sorted(anchors | set(edge)))]
                         for edge in combinations(subset_tuple, 2))
            require(len(ids) == len(set(ids)) == len(subset) * (len(subset) - 1) // 2,
                    "wrong complete internal-edge set")
            # Zero-forced forbidden columns remain explicit; no row is silently shortened.
            retained.append({"group": group, "subset": subset_tuple,
                             "ids": ids, "upper": (b_sum - 1) // 2,
                             "name": f"four_seven_blossom_group_{group}_set_"
                                     + "_".join(map(str, subset_tuple))})
        require(odd == 4096 and len(canonical) == 2048 and len(omitted) == 24
                and len(retained) == 2024, "incomplete odd-set family")
        rows.extend(sorted(retained, key=lambda row: (len(row["subset"]), row["subset"])))
        reports.append({"group": group, "outside": outside, "hub": hub,
                        "subsets_enumerated": 8192, "odd_subsets": odd,
                        "canonical": len(canonical), "omitted": len(omitted),
                        "rows": len(retained)})
    return rows, reports


def compare(base, model, expected):
    require(len(base.variables) == len(model.variables) == 4768, "wrong variable count")
    require(len(base.constraints) == 4270 and len(model.constraints) == 12366,
            "wrong constraint count")
    for i, wanted in enumerate(expected):
        row = model.constraints[4270 + i]
        require(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal,
                "wrong row type")
        require(row.name == wanted["name"], "wrong subset order/name")
        require(list(row.linear.vars) == wanted["ids"]
                and list(row.linear.coeffs) == [1] * len(wanted["ids"])
                and list(row.linear.domain) == [-(1 << 63), wanted["upper"]],
                "odd-set row differs from exhaustive raw enumeration")
    stripped = cp_model_pb2.CpModelProto()
    stripped.CopyFrom(model)
    del stripped.constraints[4270:]
    require(stripped == base, "prior proto field changed")


def controls(base, model, expected):
    mutations = {
        "coefficient": lambda m: m.constraints[4270].linear.coeffs.__setitem__(0, 2),
        "column": lambda m: m.constraints[4270].linear.vars.__setitem__(0, 4368),
        "bound": lambda m: m.constraints[4270].linear.domain.__setitem__(1, 99),
        "subset_name": lambda m: setattr(m.constraints[4270], "name", "wrong_subset"),
        "enforced": lambda m: m.constraints[4270].enforcement_literal.append(0),
        "missing": lambda m: m.constraints.pop(),
        "extra": lambda m: m.constraints.add().CopyFrom(m.constraints[4270]),
        "prior_domain": lambda m: m.variables[0].domain.__setitem__(1, 2),
        "prior_row": lambda m: m.constraints[0].linear.domain.__setitem__(1, 1),
        "hint": lambda m: (m.solution_hint.vars.append(0), m.solution_hint.values.append(1)),
    }
    report = {}
    for name, mutate in mutations.items():
        damaged = cp_model_pb2.CpModelProto()
        damaged.CopyFrom(model)
        mutate(damaged)
        try:
            compare(base, damaged, expected)
        except ValueError:
            report[name] = "rejected"
        else:
            raise ValueError(f"damaged model accepted: {name}")
    return report


def main():
    manifest = json.loads((FROZEN / "manifest.json").read_text())
    require(manifest["hashes"]["four_seven_blossom_cuts.py"] == HELPER_SHA, "wrong helper")
    for name, digest in manifest["hashes"].items():
        require(sha(FROZEN / name) == digest, "snapshot hash mismatch")
    # Pure integer arithmetic in the degree argument: 1<=d<=7 and 2d+12<=15.
    require([d for d in range(1, 8) if 2 * d + 12 <= 15] == [1], "nonhub degree argument")
    require(2 * 7 - 12 == 2, "own-hub degree argument")
    expected, groups = expected_rows()
    require(len(expected) == 8096, "wrong full family size")
    reports = []
    for case in ("cycle", "matching"):
        base_path = FROZEN / f"{case}-base.pbtxt"
        model_path = FROZEN / f"{case}-blossoms.pbtxt"
        require(sha(base_path) == BASE_SHA[case], "wrong audited base")
        base = text_format.Parse(base_path.read_text(), cp_model_pb2.CpModelProto())
        model = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
        compare(base, model, expected)
        reports.append({"case": case, "passed": True, "new_rows": 8096, "new_variables": 0,
                        "all_prior_proto_fields_preserved": True,
                        "damaged_controls": controls(base, model, expected),
                        "base_sha256": sha(base_path), "model_sha256": sha(model_path)})
        print(json.dumps({"case": case, "passed": True, "new_rows": 8096}), flush=True)
    result = {"passed": True, "groups": groups, "models": reports,
              "helper_sha256": HELPER_SHA, "checker_sha256": sha(Path(__file__)),
              "expected_rows_sha256": hashlib.sha256(json.dumps(expected).encode()).hexdigest(),
              "scope": "Elementary necessary integer odd-set inequalities in normalized "
              "regular four-sevenfold covers. No global bound or polyhedral completeness claim."}
    (HERE / "model-audit.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
