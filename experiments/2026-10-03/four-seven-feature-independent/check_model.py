# Document:    Independent Transported Feature Row Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild all feature columns from raw subsets; compare the frozen proof and proto."""

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

PROOF_SHA = "7e67ffde630c9ba27b40f6c3345ff42b2de45288dd891bd3a95dd5876a83785a"
BASE_SHA = {
    "cycle": "5cbaba3a581ab485a1ebd5adc3a328ff53c963a414fadc773bb9687abead02d9",
    "matching": "5f85a1cd9caa86742892e44c0632df0c99c0409bc3e69d0905e4924a08116b84",
}
ANCHORS = ({1, 2, 3}, {5, 6, 7}, {9, 10, 11}, {13, 14, 15})
HUBS = {4, 8, 12, 16}
GROUP = {p: i for i in range(4) for p in range(4 * i + 1, 4 * i + 5)}
GRAPHS = {"cycle": {frozenset(e) for e in ((0, 1), (1, 2), (2, 3), (0, 3))},
          "matching": {frozenset((0, 1)), frozenset((2, 3))}}
SPEC = {("cycle", "adjacent_anchor_hub"): ("<=", 3, 18),
        ("cycle", "nonadjacent_anchor_anchor"): ("<=", 2, 9),
        ("matching", "hub_hub_or_own_anchor_hub"): (">=", 1, 15),
        ("matching", "adjacent_anchor_hub"): ("<=", 2, 9),
        ("matching", "adjacent_anchor_anchor"): ("<=", 2, 9)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matches(edge, case, predicate):
    a, b = edge
    hubs = len(set(edge) & HUBS)
    same = GROUP[a] == GROUP[b]
    adjacent = frozenset((GROUP[a], GROUP[b])) in GRAPHS[case]
    return {
        "adjacent_anchor_hub": hubs == 1 and adjacent,
        "nonadjacent_anchor_anchor": hubs == 0 and not same and not adjacent,
        "hub_hub_or_own_anchor_hub": hubs == 2 or hubs == 1 and same,
        "adjacent_anchor_anchor": hubs == 0 and adjacent,
    }[predicate]


def expected_rows(proof, case):
    require(proof["valid"] is True and proof["total_linear_cuts"] == 20, "bad proof status")
    require({(r["case"], r["predicate"]) for r in proof["rules"]} == set(SPEC)
            and len(proof["rules"]) == 5, "wrong rule family")
    blocks = list(combinations(range(1, 17), 5))
    output = []
    for rule in proof["rules"]:
        rule_case, predicate = rule["case"], rule["predicate"]
        sense, bound, terms = SPEC[(rule_case, predicate)]
        require((rule["sense"], rule["bound"]) == (sense, bound), "wrong proved inequality")
        targets = rule["target_groups"]
        require(len(targets) == 4 and {t["group_index"] for t in targets} == set(range(4)),
                "incomplete target groups")
        derived = {}
        for target in targets:
            group = target["group_index"]
            require(set(target["anchor_triple"]) == ANCHORS[group]
                    and target["hub"] == 4 * (group + 1), "target labels mismatch")
            selected = {}
            for index, block in enumerate(blocks):
                block_set = set(block)
                if not ANCHORS[group] <= block_set:
                    continue
                if any(len(block_set & anchors) == 2 for anchors in ANCHORS):
                    continue
                edge = tuple(sorted(block_set - ANCHORS[group]))
                if matches(edge, rule_case, predicate):
                    selected[index] = {"edge": list(edge), "block": list(block),
                                       "variable_index": index, "coefficient": 1}
            require(len(selected) == terms, "wrong raw feature size")
            records = target["coefficients"]
            require(len(records) == terms and len({r["variable_index"] for r in records}) == terms,
                    "duplicate or missing proof terms")
            require({r["variable_index"]: r for r in records} == selected,
                    "proof columns differ from raw subsets")
            derived[group] = selected
            permutation = target["base_to_target_group_permutation"]
            point_map = target["base_to_target_point_permutation"]
            inverse = target["target_to_base_point_permutation"]
            require(sorted(permutation) == list(range(4)) and permutation[0] == group,
                    "group transport is not bijective or has wrong target")
            require(all((frozenset(pair) in GRAPHS[rule_case]) ==
                        (frozenset(permutation[i] for i in pair) in GRAPHS[rule_case])
                        for pair in combinations(range(4), 2)), "transport changes hub graph")
            require(point_map == [4 * permutation[GROUP[p]] + (p - 1) % 4 + 1
                                  for p in range(1, 17)], "wrong point transport")
            require(sorted(inverse) == list(range(1, 17))
                    and all(point_map[inverse[p - 1] - 1] == p for p in range(1, 17)),
                    "wrong inverse transport")
            if rule_case == case:
                output.append({"name": f"four_seven_feature_{case}_{predicate}_group_{group}",
                               "ids": sorted(selected), "sense": sense, "bound": bound,
                               "group": group, "predicate": predicate})
        for target in targets:
            point_map = target["base_to_target_point_permutation"]
            image = {tuple(sorted(point_map[p - 1] for p in row["block"]))
                     for row in derived[0].values()}
            require(image == {tuple(row["block"]) for row in
                              derived[target["group_index"]].values()}, "transported terms differ")
    return output


def compare(base, model, expected):
    require(len(base.variables) == 4768 and len(base.constraints) == 4270, "wrong base dimensions")
    require(len(model.variables) == 4768
            and len(model.constraints) == 4270 + len(expected), "wrong strengthened dimensions")
    for offset, wanted in enumerate(expected):
        constraint = model.constraints[4270 + offset]
        require(constraint.WhichOneof("constraint") == "linear"
                and not constraint.enforcement_literal, "wrong feature row type")
        require(constraint.name == wanted["name"], "wrong rule name/order")
        row = constraint.linear
        domain = ([-(1 << 63), wanted["bound"]] if wanted["sense"] == "<="
                  else [wanted["bound"], (1 << 63) - 1])
        require(list(row.vars) == wanted["ids"] and list(row.coeffs) == [1] * len(wanted["ids"])
                and list(row.domain) == domain, "feature row differs from proof")
    stripped = cp_model_pb2.CpModelProto()
    stripped.CopyFrom(model)
    del stripped.constraints[4270:]
    require(stripped == base, "prior proto field changed")


def damaged_controls(base, model, expected):
    controls = []

    def add(name, mutate):
        damaged = cp_model_pb2.CpModelProto()
        damaged.CopyFrom(model)
        mutate(damaged)
        controls.append((name, damaged))

    add("wrong_coefficient", lambda m: m.constraints[4270].linear.coeffs.__setitem__(0, 2))
    add("wrong_column", lambda m: m.constraints[4270].linear.vars.__setitem__(0, 4368))
    add("wrong_bound", lambda m: m.constraints[4270].linear.domain.__setitem__(1, 99))
    add("enforced_row", lambda m: m.constraints[4270].enforcement_literal.append(0))
    add("missing_row", lambda m: m.constraints.pop())
    add("extra_row", lambda m: m.constraints.add().CopyFrom(m.constraints[4270]))
    add("prior_domain", lambda m: m.variables[0].domain.__setitem__(1, 2))
    add("prior_name", lambda m: setattr(m.variables[0], "name", "damaged"))
    add("prior_row", lambda m: m.constraints[0].linear.domain.__setitem__(1, 1))
    add("new_hint", lambda m: (m.solution_hint.vars.append(0), m.solution_hint.values.append(1)))
    add("new_objective", lambda m: (m.objective.vars.append(0), m.objective.coeffs.append(1)))
    add("wrong_rule_name", lambda m: setattr(m.constraints[4270], "name", "damaged"))
    result = {}
    for name, damaged in controls:
        try:
            compare(base, damaged, expected)
        except ValueError:
            result[name] = "rejected"
        else:
            raise ValueError(f"damaged control accepted: {name}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("cycle", "matching"))
    parser.add_argument("base", type=Path)
    parser.add_argument("model", type=Path)
    parser.add_argument("proof", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require(sha(args.proof) == PROOF_SHA, "proof manifest hash mismatch")
    require(sha(args.base) == BASE_SHA[args.case], "not the audited full lifted branch base")
    proof = json.loads(args.proof.read_text())
    expected = expected_rows(proof, args.case)
    base = text_format.Parse(args.base.read_text(), cp_model_pb2.CpModelProto())
    model = text_format.Parse(args.model.read_text(), cp_model_pb2.CpModelProto())
    compare(base, model, expected)
    result = {"case": args.case, "passed": True, "all_prior_proto_fields_preserved": True,
              "new_variables": 0, "rows_checked": len(expected), "all_target_groups_checked": 4,
              "expected_rows": expected,
              "damaged_controls": damaged_controls(base, model, expected),
              "base_sha256": sha(args.base), "model_sha256": sha(args.model),
              "proof_sha256": PROOF_SHA, "checker_sha256": sha(Path(__file__)),
              "scope": "Necessary cuts only for integer full regular64-block covers in the "
              "normalized four-sevenfold branch. Transport is relabeling, not cover invariance."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("case", "passed", "rows_checked", "new_variables")}))


if __name__ == "__main__":
    main()
