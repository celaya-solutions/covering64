# Document:    Hard Top-Two Model Semantic Difference Check
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      d42c04b39560639fcc11a6c933ac28eab76986a516219477a03d2a7c82dfbf9f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Producer-side exact semantic diff; no optimizer and not the independent gate."""

import hashlib
import itertools
import json
from pathlib import Path

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LO, HI = -(1 << 63), (1 << 63) - 1


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signature(row):
    require(row.has_linear(), "unexpected non-linear row")
    return (tuple(sorted(zip(row.linear.vars, row.linear.coeffs, strict=True))),
            tuple(row.linear.domain), tuple(row.enforcement_literal))


def main():
    output = HERE / "semantic-diff-v2.json"
    require(not output.exists(), "receipt exists")
    baseline_path = HERE.parent / "compact-pair-two-counts/manifest.json"
    require(sha(baseline_path)
            == "82372b924493eed1e3a24c48e580d0b15796cc1d2c50bbe71b400bee23910aad",
            "baseline manifest hash mismatch")
    old_manifest = json.loads(baseline_path.read_text())
    new_manifest = json.loads((HERE / "manifest.json").read_text())
    old, new = cp_model.CpModel(), cp_model.CpModel()
    for model, manifest in ((old, old_manifest), (new, new_manifest)):
        path = ROOT / manifest["model_path"]
        require(sha(path) == manifest["model_sha256"], "model hash mismatch")
        require(model.proto.parse_text_format(path.read_text()), "model parse failed")
        require(not model.validate(), "model validation failed")
    require(len(old.proto.variables) == 5608 and len(new.proto.variables) == 7408, "variable count")
    require(len(old.proto.constraints) == 14404 and len(new.proto.constraints) == 3605, "row count")
    for index in range(5608):
        require(list(old.proto.variables[index].domain) == list(new.proto.variables[index].domain),
                f"base variable domain changed: {index}")
    for index in range(5608, 7408):
        require(list(new.proto.variables[index].domain) == [0, 64], "new variable domain")
    for index in range(1801):
        require(signature(old.proto.constraints[index]) == signature(new.proto.constraints[index]),
                f"cardinality/count/hole row changed: {index}")
    pairs = tuple(itertools.combinations(range(1, 17), 2))
    triples = tuple(itertools.combinations(range(1, 17), 3))
    triple_ids = {triple: 4488 + index for index, triple in enumerate(triples)}
    for pair_index, pair in enumerate(pairs):
        outside = [a for a in range(1, 17) if a not in pair]
        r, z = 4368 + pair_index, 5608 + pair_index
        ys = [5728 + 14 * pair_index + index for index in range(14)]
        offset = 1801 + 15 * pair_index
        for index, point in enumerate(outside):
            t = triple_ids[tuple(sorted((*pair, point)))]
            expected = (tuple(sorted(((ys[index], 1), (z, 1), (t, -1)))), (0, HI), ())
            require(signature(new.proto.constraints[offset + index]) == expected,
                    "hinge mismatch")
        expected = (tuple(sorted([(r, -3), (z, 2)] + [(y, 1) for y in ys])), (LO, -12), ())
        require(signature(new.proto.constraints[offset + 14]) == expected,
                "top-two budget mismatch")
    for index in range(3):
        require(signature(old.proto.constraints[14401 + index])
                == signature(new.proto.constraints[3601 + index]), "retained core row mismatch")
    expected = (tuple((index, 1) for index in sorted(new_manifest["core_rows"][3])), (LO, 55), ())
    require(signature(new.proto.constraints[3604]) == expected, "fourth core row mismatch")
    objective = new.proto.objective
    require(sorted(zip(objective.vars, objective.coeffs, strict=True))
            == [(index, 1) for index in range(5048, 5608)], "objective not exactly holes")
    require(objective.offset == 0 and objective.scaling_factor == 1, "objective scale/offset")
    require(list(new.proto.solution_hint.vars) == list(range(4368)), "hint indices")
    require(sum(new.proto.solution_hint.values) == 64, "hint cardinality")
    require(set(new.proto.solution_hint.values) <= {0, 1}, "hint Boolean values")
    receipt = {
        "passed": True, "optimizer_calls": 0, "independent_gate": False,
        "source_sha256": sha(__file__), "manifest_sha256": sha(HERE / "manifest.json"),
        "baseline_manifest_sha256": sha(baseline_path),
        "old_model_sha256": old_manifest["model_sha256"],
        "new_model_sha256": new_manifest["model_sha256"],
        "unchanged_base_variable_domains": 5608, "new_integer_variables_0_to_64": 1800,
        "unchanged_cardinality_count_hole_rows": 1801, "retained_original_core_rows": 3,
        "new_fourth_core_rows": 1, "new_hinge_rows": 1680, "new_top_two_budget_rows": 120,
        "omitted_single_triple_rows": 1680, "replaced_explicit_two_triple_rows": 10920,
        "objective": "sum of exact 560 hole flags; unit coefficients, offset0, scale1",
        "hint": "4368 block-only Boolean positions, 64 ones; infeasible H49 guidance",
        "all_new_rows_accounted": True, "requires_independent_serialized_model_gate": True,
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "optimizer_calls": 0, "receipt_sha256": sha(output)}))


if __name__ == "__main__":
    main()
